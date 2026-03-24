from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from groups_app.models import Group, GroupMember

from .models import Expense
from .serializers import ExpenseCreateSerializer, ExpenseSerializer


def _ensure_group_member(user, group):
	is_member = GroupMember.objects.filter(user=user, group=group).exists()
	if not is_member:
		raise PermissionDenied("You are not a member of this group.")


class GroupExpenseListCreateView(APIView):
	def get(self, request, group_id):
		group = get_object_or_404(Group, pk=group_id)
		_ensure_group_member(request.user, group)

		expenses = (
			Expense.objects.filter(group=group)
			.select_related("paid_by")
			.prefetch_related("splits__user")
			.order_by("-expense_date", "-created_at")
		)
		serializer = ExpenseSerializer(expenses, many=True)

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

		serializer = ExpenseCreateSerializer(data=request.data, context={"group": group})
		serializer.is_valid(raise_exception=True)
		expense = serializer.save()

		return Response(
			{
				"message": "Expense created successfully.",
				"expense": ExpenseSerializer(
					expense,
					context={"request": request},
				).data,
			},
			status=status.HTTP_201_CREATED,
		)


class GroupExpenseDetailView(APIView):
	def get(self, request, group_id, expense_id):
		group = get_object_or_404(Group, pk=group_id)
		_ensure_group_member(request.user, group)

		expense = get_object_or_404(
			Expense.objects.select_related("paid_by").prefetch_related("splits__user"),
			pk=expense_id,
			group=group,
		)

		return Response(ExpenseSerializer(expense).data, status=status.HTTP_200_OK)
