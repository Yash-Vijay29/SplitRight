import base64
import json
import mimetypes
from datetime import date
from decimal import Decimal, InvalidOperation

import httpx
from django.conf import settings
from rest_framework import status


ALLOWED_BILL_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


class BillParsingError(Exception):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _to_money_string(value, default="0.00"):
    if value in (None, ""):
        return default

    try:
        normalized = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return default

    return f"{normalized:.2f}"


def _normalize_date(value):
    if not value:
        return date.today().isoformat()

    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return date.today().isoformat()

    return date.today().isoformat()


def _extract_json(raw_content):
    content = (raw_content or "").strip()
    if not content:
        raise BillParsingError("No response was returned by the bill parser.", status.HTTP_502_BAD_GATEWAY)

    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise BillParsingError(
            "Bill parser returned an invalid format. Please try another image.",
            status.HTTP_502_BAD_GATEWAY,
        ) from exc


def _normalize_charges(charges):
    normalized = []
    for entry in charges or []:
        if not isinstance(entry, dict):
            continue

        name = str(entry.get("name") or entry.get("description") or "Line item").strip()
        quantity = entry.get("quantity", 1)
        unit_price = _to_money_string(entry.get("unit_price"))
        line_total = _to_money_string(entry.get("line_total") or entry.get("amount"))
        normalized.append(
            {
                "name": name,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    return normalized


def _guess_content_type(uploaded_file):
    if uploaded_file.content_type:
        return uploaded_file.content_type

    guessed_type, _ = mimetypes.guess_type(uploaded_file.name or "")
    return guessed_type or ""


def _normalize_party_size(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None

    if parsed <= 0:
        return None

    return parsed


def parse_bill_image_with_openrouter(uploaded_file):
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise BillParsingError(
            "Bill parser is not configured. Set OPENROUTER_API_KEY.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    max_bytes = int(settings.BILL_UPLOAD_MAX_MB * 1024 * 1024)
    if uploaded_file.size > max_bytes:
        raise BillParsingError(
            f"Bill image is too large. Max size is {settings.BILL_UPLOAD_MAX_MB:g} MB.",
            status.HTTP_400_BAD_REQUEST,
        )

    content_type = _guess_content_type(uploaded_file)
    if content_type not in ALLOWED_BILL_CONTENT_TYPES:
        raise BillParsingError(
            "Unsupported file type. Upload JPEG, PNG, or WEBP images only.",
            status.HTTP_400_BAD_REQUEST,
        )

    image_bytes = uploaded_file.read()
    if not image_bytes:
        raise BillParsingError("Uploaded file is empty.", status.HTTP_400_BAD_REQUEST)

    encoded_image = base64.b64encode(image_bytes).decode("ascii")

    extraction_prompt = (
        "Extract receipt details and return ONLY valid JSON with this schema: "
        "{"
        "\"merchant_name\": string,"
        "\"bill_date\": string (YYYY-MM-DD or empty),"
        "\"party_size\": number|null,"
        "\"currency\": string ISO code like USD/INR,"
        "\"extracted_charges\": ["
        "{\"name\": string, \"quantity\": number, \"unit_price\": number|string, \"line_total\": number|string}"
        "],"
        "\"totals\": {"
        "\"subtotal\": number|string|null,"
        "\"tax\": number|string|null,"
        "\"tip\": number|string|null,"
        "\"discounts\": number|string|null,"
        "\"total\": number|string|null"
        "},"
        "\"warnings\": [string],"
        "\"confidence\": number"
        "}. "
        "Never include markdown fences or extra text."
    )

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": extraction_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{encoded_image}",
                        },
                    },
                ],
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=settings.BILL_AI_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise BillParsingError(
            "Unable to reach bill parser service right now. Please try again.",
            status.HTTP_502_BAD_GATEWAY,
        ) from exc

    if response.status_code >= 400:
        raise BillParsingError(
            "Bill parser request failed. Please try another image.",
            status.HTTP_502_BAD_GATEWAY,
        )

    completion_payload = response.json()
    content = (
        completion_payload.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    extracted = _extract_json(content)

    extracted_charges = _normalize_charges(extracted.get("extracted_charges"))
    totals = extracted.get("totals") or {}

    total_amount = _to_money_string(totals.get("total"))
    subtotal = _to_money_string(totals.get("subtotal"))
    tax = _to_money_string(totals.get("tax"))
    tip = _to_money_string(totals.get("tip"))
    discounts = _to_money_string(totals.get("discounts"))

    merchant_name = str(extracted.get("merchant_name") or "Bill Upload").strip()
    bill_date = _normalize_date(extracted.get("bill_date"))
    currency = str(extracted.get("currency") or "USD").upper()

    warnings = extracted.get("warnings")
    if not isinstance(warnings, list):
        warnings = []

    party_size = _normalize_party_size(extracted.get("party_size"))

    return {
        "extracted_charges": extracted_charges,
        "totals": {
            "subtotal": subtotal,
            "tax": tax,
            "tip": tip,
            "discounts": discounts,
            "total": total_amount,
            "currency": currency,
        },
        "suggested_expense": {
            "amount": total_amount,
            "expense_date": bill_date,
            "description": merchant_name,
        },
        "warnings": [str(item) for item in warnings],
        "confidence": extracted.get("confidence"),
        "party_size": party_size,
    }
