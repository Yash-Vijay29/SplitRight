from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from accounts.serializers import UserSerializer
from groups_app.models import GroupMember

from .models import Expense, ExpenseSplit


class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = ["expense_split_id", "user", "share_amount"]


class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    group_id = serializers.IntegerField(read_only=True)
    splits = ExpenseSplitSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = [
            "expense_id",
            "group_id",
            "paid_by",
            "amount",
            "expense_date",
            "description",
            "created_at",
            "splits",
        ]


class ExpenseSplitInputSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    share_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))


class ExpenseCreateSerializer(serializers.Serializer):
    paid_by = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    expense_date = serializers.DateField()
    description = serializers.CharField(max_length=255, allow_blank=True, required=False, default="")
    split_type = serializers.ChoiceField(choices=["equal", "unequal"])
    split_user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False,
    )
    splits = ExpenseSplitInputSerializer(many=True, required=False, allow_empty=False)

    def _to_cents(self, amount: Decimal) -> int:
        return int((amount * 100).quantize(Decimal("1")))

    def _cents_to_amount(self, cents: int) -> Decimal:
        return (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"))

    def validate(self, attrs):
        group = self.context.get("group")
        if group is None:
            raise serializers.ValidationError("Group context is required.")

        member_ids = set(
            GroupMember.objects.filter(group=group).values_list("user_id", flat=True)
        )
        if attrs["paid_by"] not in member_ids:
            raise serializers.ValidationError(
                {"paid_by": "Payer must be a member of the group."}
            )

        split_type = attrs["split_type"]
        amount = attrs["amount"]

        if split_type == "equal":
            split_user_ids = attrs.get("split_user_ids")
            if not split_user_ids:
                raise serializers.ValidationError(
                    {"split_user_ids": "split_user_ids is required for equal split."}
                )

            if len(split_user_ids) != len(set(split_user_ids)):
                raise serializers.ValidationError(
                    {"split_user_ids": "Duplicate users are not allowed in split_user_ids."}
                )

            invalid_users = [user_id for user_id in split_user_ids if user_id not in member_ids]
            if invalid_users:
                raise serializers.ValidationError(
                    {"split_user_ids": "All split users must be members of the group."}
                )

            total_cents = self._to_cents(amount)
            user_count = len(split_user_ids)
            base_share = total_cents // user_count
            remainder = total_cents % user_count

            normalized_splits = []
            for index, user_id in enumerate(split_user_ids):
                extra_cent = 1 if index < remainder else 0
                cents = base_share + extra_cent
                normalized_splits.append(
                    {
                        "user_id": user_id,
                        "share_amount": self._cents_to_amount(cents),
                    }
                )

        else:
            raw_splits = attrs.get("splits")
            if not raw_splits:
                raise serializers.ValidationError({"splits": "splits is required for unequal split."})

            split_user_ids = [entry["user_id"] for entry in raw_splits]
            if len(split_user_ids) != len(set(split_user_ids)):
                raise serializers.ValidationError(
                    {"splits": "Duplicate users are not allowed in splits."}
                )

            invalid_users = [user_id for user_id in split_user_ids if user_id not in member_ids]
            if invalid_users:
                raise serializers.ValidationError(
                    {"splits": "All split users must be members of the group."}
                )

            split_sum = sum((entry["share_amount"] for entry in raw_splits), Decimal("0"))
            if split_sum != amount:
                raise serializers.ValidationError(
                    {"splits": "Sum of split shares must equal expense amount."}
                )

            normalized_splits = [
                {
                    "user_id": entry["user_id"],
                    "share_amount": entry["share_amount"],
                }
                for entry in raw_splits
            ]

        attrs["normalized_splits"] = normalized_splits
        return attrs

    def create(self, validated_data):
        group = self.context["group"]

        with transaction.atomic():
            expense = Expense.objects.create(
                group=group,
                paid_by_id=validated_data["paid_by"],
                amount=validated_data["amount"],
                expense_date=validated_data["expense_date"],
                description=validated_data.get("description", ""),
            )

            for split in validated_data["normalized_splits"]:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=split["user_id"],
                    share_amount=split["share_amount"],
                )

        return expense


class ExpenseBillParseSerializer(serializers.Serializer):
    bill_image = serializers.FileField(required=True)