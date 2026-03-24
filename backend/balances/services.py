from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum

from expenses.models import Expense, ExpenseSplit
from groups_app.models import GroupMember
from settlements.models import Settlement


ZERO = Decimal("0.00")


def _as_money(value):
    return value.quantize(Decimal("0.01"))


def _serialize_money(value):
    return f"{_as_money(value):.2f}"


def _status_from_net(net_amount):
    if net_amount > ZERO:
        return "gets_back"
    if net_amount < ZERO:
        return "owes"
    return "settled"


def _load_group_member_rows(group):
    return list(
        GroupMember.objects.filter(group=group)
        .select_related("user")
        .order_by("joined_at", "user_id")
    )


def _build_aggregate_map(queryset, key_field):
    totals = defaultdict(lambda: ZERO)
    for row in queryset:
        key = row[key_field]
        totals[key] = _as_money(row["total"] or ZERO)
    return totals


def build_group_balances(group):
    memberships = _load_group_member_rows(group)
    member_ids = [membership.user_id for membership in memberships]

    paid_map = _build_aggregate_map(
        Expense.objects.filter(group=group)
        .values("paid_by_id")
        .annotate(total=Sum("amount")),
        key_field="paid_by_id",
    )
    owed_map = _build_aggregate_map(
        ExpenseSplit.objects.filter(expense__group=group)
        .values("user_id")
        .annotate(total=Sum("share_amount")),
        key_field="user_id",
    )
    settlement_sent_map = _build_aggregate_map(
        Settlement.objects.filter(group=group)
        .values("from_user_id")
        .annotate(total=Sum("amount")),
        key_field="from_user_id",
    )
    settlement_received_map = _build_aggregate_map(
        Settlement.objects.filter(group=group)
        .values("to_user_id")
        .annotate(total=Sum("amount")),
        key_field="to_user_id",
    )

    rows = []
    for membership in memberships:
        user = membership.user
        paid = paid_map[user.user_id]
        owed = owed_map[user.user_id]
        sent = settlement_sent_map[user.user_id]
        received = settlement_received_map[user.user_id]
        net = _as_money(paid - owed - sent + received)

        rows.append(
            {
                "user": {
                    "user_id": user.user_id,
                    "name": user.name,
                    "email": user.email,
                    "created_at": user.created_at,
                },
                "total_paid": _serialize_money(paid),
                "total_owed": _serialize_money(owed),
                "settlement_sent": _serialize_money(sent),
                "settlement_received": _serialize_money(received),
                "net_balance": _serialize_money(net),
                "status": _status_from_net(net),
            }
        )

    total_paid = sum((paid_map[user_id] for user_id in member_ids), ZERO)
    total_owed = sum((owed_map[user_id] for user_id in member_ids), ZERO)
    total_settlement_sent = sum((settlement_sent_map[user_id] for user_id in member_ids), ZERO)
    total_settlement_received = sum(
        (settlement_received_map[user_id] for user_id in member_ids),
        ZERO,
    )

    return {
        "group_id": group.group_id,
        "group_name": group.group_name,
        "count": len(rows),
        "results": rows,
        "summary": {
            "total_paid": _serialize_money(total_paid),
            "total_owed": _serialize_money(total_owed),
            "total_settlement_sent": _serialize_money(total_settlement_sent),
            "total_settlement_received": _serialize_money(total_settlement_received),
        },
    }


def _add_debt(owes_map, debtor_id, creditor_id, amount):
    amount = _as_money(amount)
    if debtor_id == creditor_id or amount <= ZERO:
        return

    forward_key = (debtor_id, creditor_id)
    reverse_key = (creditor_id, debtor_id)

    reverse_amount = owes_map.get(reverse_key, ZERO)
    if reverse_amount > ZERO:
        if reverse_amount > amount:
            owes_map[reverse_key] = _as_money(reverse_amount - amount)
            return
        if reverse_amount == amount:
            owes_map.pop(reverse_key, None)
            return
        owes_map.pop(reverse_key, None)
        amount = _as_money(amount - reverse_amount)

    owes_map[forward_key] = _as_money(owes_map.get(forward_key, ZERO) + amount)


def build_group_pairwise_owes(group):
    owes_map = {}

    expense_rows = ExpenseSplit.objects.filter(expense__group=group).values(
        "user_id",
        "share_amount",
        "expense__paid_by_id",
    )
    for row in expense_rows:
        debtor_id = row["user_id"]
        creditor_id = row["expense__paid_by_id"]
        _add_debt(owes_map, debtor_id, creditor_id, row["share_amount"])

    settlement_rows = Settlement.objects.filter(group=group).values(
        "from_user_id",
        "to_user_id",
        "amount",
    )
    for row in settlement_rows:
        # A settlement from A->B reduces any A owes B. If it overpays, B owes A.
        _add_debt(owes_map, row["to_user_id"], row["from_user_id"], row["amount"])

    user_membership = {
        membership.user_id: membership.user
        for membership in GroupMember.objects.filter(group=group).select_related("user")
    }

    results = []
    for (from_user_id, to_user_id), amount in sorted(owes_map.items()):
        if amount <= ZERO:
            continue

        from_user = user_membership.get(from_user_id)
        to_user = user_membership.get(to_user_id)
        if from_user is None or to_user is None:
            continue

        results.append(
            {
                "from_user": {
                    "user_id": from_user.user_id,
                    "name": from_user.name,
                    "email": from_user.email,
                },
                "to_user": {
                    "user_id": to_user.user_id,
                    "name": to_user.name,
                    "email": to_user.email,
                },
                "amount": _serialize_money(amount),
            }
        )

    return results
