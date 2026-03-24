from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from groups_app.models import Group, GroupMember

from .models import Settlement
from .serializers import SettlementCreateSerializer, SettlementSerializer


def _ensure_group_member(user, group):
	is_member = GroupMember.objects.filter(user=user, group=group).exists()
	if not is_member:
		raise PermissionDenied("You are not a member of this group.")


class GroupSettlementListCreateView(APIView):
	def get(self, request, group_id):
		group = get_object_or_404(Group, pk=group_id)
		_ensure_group_member(request.user, group)

		settlements = (
			Settlement.objects.filter(group=group)
			.select_related("from_user", "to_user")
			.order_by("-settlement_date", "-created_at")
		)
		serializer = SettlementSerializer(settlements, many=True)

		return Response(
			{
				"group_id": group.group_id,
				"count": len(serializer.data),
				"results": serializer.data,
			},
			status=status.HTTP_200_OK,
		)

	def post(self, request, group_id):
		group = get_object_or_404(Group, pk=group_id)
		_ensure_group_member(request.user, group)

		serializer = SettlementCreateSerializer(data=request.data, context={"group": group})
		serializer.is_valid(raise_exception=True)
		settlement = serializer.save()

		return Response(
			{
				"message": "Settlement recorded successfully.",
				"settlement": SettlementSerializer(settlement).data,
			},
			status=status.HTTP_201_CREATED,
		)
