from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from groups_app.models import Group, GroupMember

from .models import Expense, ExpenseSplit
from .services import BillParsingError, parse_bill_image_with_openrouter


class ExpenseApiTests(APITestCase):
	def setUp(self):
		self.owner = User.objects.create_user(
			email="owner@example.com",
			name="Owner",
			password="pass12345",
		)
		self.member = User.objects.create_user(
			email="member@example.com",
			name="Member",
			password="pass12345",
		)
		self.member_two = User.objects.create_user(
			email="member2@example.com",
			name="Member Two",
			password="pass12345",
		)
		self.stranger = User.objects.create_user(
			email="stranger@example.com",
			name="Stranger",
			password="pass12345",
		)

		self.group = Group.objects.create(group_name="Trip", created_by=self.owner)
		GroupMember.objects.create(group=self.group, user=self.owner)
		GroupMember.objects.create(group=self.group, user=self.member)
		GroupMember.objects.create(group=self.group, user=self.member_two)

		self.list_create_url = f"/api/groups/{self.group.group_id}/expenses"

	def test_create_equal_split_stores_correctly(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"paid_by": self.owner.user_id,
			"amount": "100.00",
			"expense_date": str(date.today()),
			"description": "Dinner",
			"split_type": "equal",
			"split_user_ids": [self.owner.user_id, self.member.user_id],
		}

		response = self.client.post(self.list_create_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Expense.objects.count(), 1)
		self.assertEqual(ExpenseSplit.objects.count(), 2)

		expense = Expense.objects.first()
		shares = list(
			ExpenseSplit.objects.filter(expense=expense)
			.order_by("user_id")
			.values_list("share_amount", flat=True)
		)
		self.assertEqual(shares, [Decimal("50.00"), Decimal("50.00")])

	def test_create_unequal_split_stores_correctly(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"paid_by": self.owner.user_id,
			"amount": "120.00",
			"expense_date": str(date.today()),
			"description": "Cab + Snacks",
			"split_type": "unequal",
			"splits": [
				{"user_id": self.owner.user_id, "share_amount": "20.00"},
				{"user_id": self.member.user_id, "share_amount": "40.00"},
				{"user_id": self.member_two.user_id, "share_amount": "60.00"},
			],
		}

		response = self.client.post(self.list_create_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Expense.objects.count(), 1)
		self.assertEqual(ExpenseSplit.objects.count(), 3)

		expense = Expense.objects.first()
		split_map = {
			split.user_id: split.share_amount
			for split in ExpenseSplit.objects.filter(expense=expense)
		}
		self.assertEqual(split_map[self.owner.user_id], Decimal("20.00"))
		self.assertEqual(split_map[self.member.user_id], Decimal("40.00"))
		self.assertEqual(split_map[self.member_two.user_id], Decimal("60.00"))

	def test_split_sum_mismatch_rejects_and_rolls_back(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"paid_by": self.owner.user_id,
			"amount": "100.00",
			"expense_date": str(date.today()),
			"description": "Bad split",
			"split_type": "unequal",
			"splits": [
				{"user_id": self.owner.user_id, "share_amount": "30.00"},
				{"user_id": self.member.user_id, "share_amount": "20.00"},
			],
		}

		response = self.client.post(self.list_create_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(Expense.objects.count(), 0)
		self.assertEqual(ExpenseSplit.objects.count(), 0)

	def test_payer_not_in_group_is_rejected(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"paid_by": self.stranger.user_id,
			"amount": "90.00",
			"expense_date": str(date.today()),
			"description": "Invalid payer",
			"split_type": "equal",
			"split_user_ids": [self.owner.user_id, self.member.user_id],
		}

		response = self.client.post(self.list_create_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("paid_by", response.data)
		self.assertEqual(Expense.objects.count(), 0)

	def test_non_member_cannot_list_or_create_expenses(self):
		self.client.force_authenticate(user=self.stranger)

		list_response = self.client.get(self.list_create_url)
		self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)

		payload = {
			"paid_by": self.owner.user_id,
			"amount": "100.00",
			"expense_date": str(date.today()),
			"description": "Dinner",
			"split_type": "equal",
			"split_user_ids": [self.owner.user_id, self.member.user_id],
		}
		create_response = self.client.post(self.list_create_url, payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

	def test_list_and_detail_return_split_details(self):
		self.client.force_authenticate(user=self.owner)
		expense = Expense.objects.create(
			group=self.group,
			paid_by=self.owner,
			amount=Decimal("90.00"),
			expense_date=date.today(),
			description="Museum tickets",
		)
		ExpenseSplit.objects.create(expense=expense, user=self.owner, share_amount=Decimal("30.00"))
		ExpenseSplit.objects.create(expense=expense, user=self.member, share_amount=Decimal("30.00"))
		ExpenseSplit.objects.create(expense=expense, user=self.member_two, share_amount=Decimal("30.00"))

		list_response = self.client.get(self.list_create_url)
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(list_response.data["count"], 1)
		self.assertEqual(len(list_response.data["results"][0]["splits"]), 3)

		detail_url = f"/api/groups/{self.group.group_id}/expenses/{expense.expense_id}"
		detail_response = self.client.get(detail_url)
		self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
		self.assertEqual(detail_response.data["expense_id"], expense.expense_id)
		self.assertEqual(len(detail_response.data["splits"]), 3)

	def test_expense_split_user_must_be_group_member(self):
		expense = Expense.objects.create(
			group=self.group,
			paid_by=self.owner,
			amount=Decimal("50.00"),
			expense_date=date.today(),
			description="Invalid split user",
		)

		with self.assertRaises(ValidationError):
			ExpenseSplit.objects.create(
				expense=expense,
				user=self.stranger,
				share_amount=Decimal("50.00"),
			)


class ExpenseBillParseApiTests(APITestCase):
	def setUp(self):
		self.owner = User.objects.create_user(
			email="owner@example.com",
			name="Owner",
			password="pass12345",
		)
		self.member = User.objects.create_user(
			email="member@example.com",
			name="Member",
			password="pass12345",
		)
		self.stranger = User.objects.create_user(
			email="stranger@example.com",
			name="Stranger",
			password="pass12345",
		)

		self.group = Group.objects.create(group_name="Trip", created_by=self.owner)
		GroupMember.objects.create(group=self.group, user=self.owner)
		GroupMember.objects.create(group=self.group, user=self.member)

		self.url = f"/api/groups/{self.group.group_id}/expenses/parse-bill"

	@patch("expenses.views.parse_bill_image_with_openrouter")
	def test_member_can_parse_bill(self, parse_mock):
		self.client.force_authenticate(user=self.owner)
		parse_mock.return_value = {
			"extracted_charges": [{"name": "Burger", "quantity": 1, "unit_price": "9.00", "line_total": "9.00"}],
			"totals": {
				"subtotal": "9.00",
				"tax": "1.00",
				"tip": "0.00",
				"discounts": "0.00",
				"total": "10.00",
				"currency": "USD",
			},
			"suggested_expense": {
				"amount": "10.00",
				"expense_date": str(date.today()),
				"description": "Test Cafe",
			},
			"warnings": [],
			"confidence": 0.98,
		}

		bill_image = SimpleUploadedFile("bill.png", b"fake-image-content", content_type="image/png")
		response = self.client.post(self.url, {"bill_image": bill_image}, format="multipart")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["suggested_expense"]["amount"], "10.00")
		self.assertEqual(response.data["totals"]["currency"], "USD")
		self.assertEqual(len(response.data["extracted_charges"]), 1)
		self.assertTrue(parse_mock.called)

	@patch("expenses.views.parse_bill_image_with_openrouter")
	def test_non_member_cannot_parse_bill(self, parse_mock):
		self.client.force_authenticate(user=self.stranger)
		bill_image = SimpleUploadedFile("bill.png", b"fake-image-content", content_type="image/png")

		response = self.client.post(self.url, {"bill_image": bill_image}, format="multipart")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		parse_mock.assert_not_called()

	def test_missing_file_is_rejected(self):
		self.client.force_authenticate(user=self.owner)

		response = self.client.post(self.url, {}, format="multipart")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("bill_image", response.data)

	@patch("expenses.views.parse_bill_image_with_openrouter")
	def test_service_error_is_returned(self, parse_mock):
		self.client.force_authenticate(user=self.owner)
		parse_mock.side_effect = BillParsingError(
			"Bill parser is not configured.",
			status.HTTP_503_SERVICE_UNAVAILABLE,
		)

		bill_image = SimpleUploadedFile("bill.png", b"fake-image-content", content_type="image/png")
		response = self.client.post(self.url, {"bill_image": bill_image}, format="multipart")

		self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
		self.assertEqual(response.data["detail"], "Bill parser is not configured.")


class ExpenseBillParsingServiceTests(APITestCase):
	@override_settings(
		OPENROUTER_API_KEY="test-key",
		OPENROUTER_MODEL="openai/gpt-4o-mini",
		OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
		BILL_UPLOAD_MAX_MB=8,
		BILL_AI_TIMEOUT_SECONDS=5,
	)
	def test_rejects_unsupported_file_type(self):
		bad_file = SimpleUploadedFile("bill.txt", b"not-image", content_type="text/plain")

		with self.assertRaises(BillParsingError) as ctx:
			parse_bill_image_with_openrouter(bad_file)

		self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("Unsupported file type", ctx.exception.message)

	@override_settings(
		OPENROUTER_API_KEY="test-key",
		OPENROUTER_MODEL="openai/gpt-4o-mini",
		OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
		BILL_UPLOAD_MAX_MB=8,
		BILL_AI_TIMEOUT_SECONDS=5,
	)
	@patch("expenses.services.httpx.Client")
	def test_normalizes_successful_openrouter_response(self, client_mock):
		client_instance = MagicMock()
		client_mock.return_value.__enter__.return_value = client_instance

		response_mock = MagicMock()
		response_mock.status_code = 200
		response_mock.json.return_value = {
			"choices": [
				{
					"message": {
						"content": (
							'{"merchant_name":"Cafe Rio","bill_date":"2026-04-15","party_size":3,"currency":"usd",'
							'"extracted_charges":[{"name":"Pasta","quantity":2,"unit_price":10,"line_total":20}],'
							'"totals":{"subtotal":20,"tax":2,"tip":3,"discounts":0,"total":25},'
							'"warnings":["Low clarity near footer"],"confidence":0.91}'
						)
					}
				}
			]
		}
		client_instance.post.return_value = response_mock

		bill_image = SimpleUploadedFile("bill.png", b"fake-image-content", content_type="image/png")
		result = parse_bill_image_with_openrouter(bill_image)

		self.assertEqual(result["suggested_expense"]["amount"], "25.00")
		self.assertEqual(result["suggested_expense"]["description"], "Cafe Rio")
		self.assertEqual(result["totals"]["currency"], "USD")
		self.assertEqual(result["totals"]["tax"], "2.00")
		self.assertEqual(len(result["extracted_charges"]), 1)
		self.assertEqual(result["warnings"], ["Low clarity near footer"])
		self.assertEqual(result["party_size"], 3)
