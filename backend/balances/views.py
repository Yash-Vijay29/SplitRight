from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import UserSerializer
from groups_app.models import Group, GroupMember

from .services import build_group_balances, build_group_pairwise_owes


def _ensure_group_member(user, group):
	is_member = GroupMember.objects.filter(user=user, group=group).exists()
	if not is_member:
		raise PermissionDenied("You are not a member of this group.")


class GroupBalancesView(APIView):
	def get(self, request, group_id):
		group = get_object_or_404(Group, pk=group_id)
		_ensure_group_member(request.user, group)

		balance_payload = build_group_balances(group)
		return Response(balance_payload, status=status.HTTP_200_OK)


class GroupPairwiseBalancesView(APIView):
	def get(self, request, group_id):
		group = get_object_or_404(Group, pk=group_id)
		_ensure_group_member(request.user, group)

		pairwise_rows = build_group_pairwise_owes(group)

		return Response(
			{
				"group_id": group.group_id,
				"group_name": group.group_name,
				"count": len(pairwise_rows),
				"results": pairwise_rows,
			},
			status=status.HTTP_200_OK,
		)


class MyBalancesView(APIView):
	def get(self, request):
		memberships = GroupMember.objects.filter(user=request.user).select_related("group")

		per_group_rows = []
		overall_paid = Decimal("0.00")
		overall_owed = Decimal("0.00")
		overall_settlement_sent = Decimal("0.00")
		overall_settlement_received = Decimal("0.00")
		overall_net = Decimal("0.00")

		for membership in memberships:
			group = membership.group
			group_balances = build_group_balances(group)

			my_row = next(
				(
					row
					for row in group_balances["results"]
					if row["user"]["user_id"] == request.user.user_id
				),
				None,
			)
			if my_row is None:
				continue

			per_group_rows.append(
				{
					"group_id": group.group_id,
					"group_name": group.group_name,
					"total_paid": my_row["total_paid"],
					"total_owed": my_row["total_owed"],
					"settlement_sent": my_row["settlement_sent"],
					"settlement_received": my_row["settlement_received"],
					"net_balance": my_row["net_balance"],
					"status": my_row["status"],
				}
			)

			overall_paid += Decimal(my_row["total_paid"])
			overall_owed += Decimal(my_row["total_owed"])
			overall_settlement_sent += Decimal(my_row["settlement_sent"])
			overall_settlement_received += Decimal(my_row["settlement_received"])
			overall_net += Decimal(my_row["net_balance"])

		return Response(
			{
				"user": UserSerializer(request.user).data,
				"totals": {
					"total_paid": f"{overall_paid.quantize(Decimal('0.01')):.2f}",
					"total_owed": f"{overall_owed.quantize(Decimal('0.01')):.2f}",
					"settlement_sent": f"{overall_settlement_sent.quantize(Decimal('0.01')):.2f}",
					"settlement_received": f"{overall_settlement_received.quantize(Decimal('0.01')):.2f}",
					"net_balance": f"{overall_net.quantize(Decimal('0.01')):.2f}",
				},
				"count": len(per_group_rows),
				"results": per_group_rows,
			},
			status=status.HTTP_200_OK,
		)
