from decimal import Decimal

from rest_framework import serializers

from accounts.serializers import UserSerializer
from groups_app.models import GroupMember

from .models import Settlement


class SettlementSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    group_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Settlement
        fields = [
            "settlement_id",
            "from_user",
            "to_user",
            "group_id",
            "amount",
            "settlement_date",
            "created_at",
        ]


class SettlementCreateSerializer(serializers.Serializer):
    from_user = serializers.IntegerField(min_value=1)
    to_user = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    settlement_date = serializers.DateField()

    def validate(self, attrs):
        group = self.context.get("group")
        if group is None:
            raise serializers.ValidationError("Group context is required.")

        from_user_id = attrs["from_user"]
        to_user_id = attrs["to_user"]

        if from_user_id == to_user_id:
            raise serializers.ValidationError(
                {"to_user": "from_user and to_user must be different."}
            )

        member_ids = set(
            GroupMember.objects.filter(group=group).values_list("user_id", flat=True)
        )
        if from_user_id not in member_ids:
            raise serializers.ValidationError(
                {"from_user": "from_user must be a member of the group."}
            )
        if to_user_id not in member_ids:
            raise serializers.ValidationError(
                {"to_user": "to_user must be a member of the group."}
            )

        return attrs

    def create(self, validated_data):
        group = self.context["group"]
        return Settlement.objects.create(
            group=group,
            from_user_id=validated_data["from_user"],
            to_user_id=validated_data["to_user"],
            amount=validated_data["amount"],
            settlement_date=validated_data["settlement_date"],
        )