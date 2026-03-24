from django.db import transaction
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Group, GroupMember


class GroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Group
        fields = ["group_id", "group_name", "created_by", "created_at"]


class GroupCreateSerializer(serializers.Serializer):
    group_name = serializers.CharField(max_length=150)

    def validate_group_name(self, value):
        group_name = value.strip()
        if not group_name:
            raise serializers.ValidationError("group_name cannot be empty.")
        return group_name

    def create(self, validated_data):
        request = self.context["request"]

        with transaction.atomic():
            group = Group.objects.create(
                group_name=validated_data["group_name"],
                created_by=request.user,
            )
            GroupMember.objects.create(group=group, user=request.user)

        return group


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMember
        fields = ["group_member_id", "user", "joined_at"]
