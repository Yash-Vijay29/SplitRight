from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from expenses.models import Expense, ExpenseSplit
from groups_app.models import Group, GroupMember
from settlements.models import Settlement


class BalanceApiTests(APITestCase):
	def setUp(self):
		self.user_a = User.objects.create_user(
			email="a@example.com",
			name="User A",
			password="pass12345",
		)
		self.user_b = User.objects.create_user(
			email="b@example.com",
			name="User B",
			password="pass12345",
		)
		self.user_c = User.objects.create_user(
			email="c@example.com",
			name="User C",
			password="pass12345",
		)
		self.stranger = User.objects.create_user(
			email="stranger@example.com",
			name="Stranger",
			password="pass12345",
		)

		self.group = Group.objects.create(group_name="Trip", created_by=self.user_a)
		GroupMember.objects.create(group=self.group, user=self.user_a)
		GroupMember.objects.create(group=self.group, user=self.user_b)
		GroupMember.objects.create(group=self.group, user=self.user_c)

		expense_1 = Expense.objects.create(
			group=self.group,
			paid_by=self.user_a,
			amount=Decimal("120.00"),
			expense_date=date.today(),
			description="Hotel",
		)
		ExpenseSplit.objects.create(expense=expense_1, user=self.user_a, share_amount=Decimal("40.00"))
		ExpenseSplit.objects.create(expense=expense_1, user=self.user_b, share_amount=Decimal("40.00"))
		ExpenseSplit.objects.create(expense=expense_1, user=self.user_c, share_amount=Decimal("40.00"))

		expense_2 = Expense.objects.create(
			group=self.group,
			paid_by=self.user_b,
			amount=Decimal("60.00"),
			expense_date=date.today(),
			description="Cab",
		)
		ExpenseSplit.objects.create(expense=expense_2, user=self.user_a, share_amount=Decimal("20.00"))
		ExpenseSplit.objects.create(expense=expense_2, user=self.user_b, share_amount=Decimal("20.00"))
		ExpenseSplit.objects.create(expense=expense_2, user=self.user_c, share_amount=Decimal("20.00"))

		Settlement.objects.create(
			group=self.group,
			from_user=self.user_c,
			to_user=self.user_a,
			amount=Decimal("15.00"),
			settlement_date=date.today(),
		)

		self.group_balances_url = f"/api/groups/{self.group.group_id}/balances"
		self.group_pairwise_url = f"/api/groups/{self.group.group_id}/balances/pairwise"
		self.my_balances_url = "/api/users/me/balances"

	def test_group_balances_include_settlements_in_net(self):
		self.client.force_authenticate(user=self.user_a)

		response = self.client.get(self.group_balances_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["count"], 3)

		rows_by_user = {row["user"]["user_id"]: row for row in response.data["results"]}

		self.assertEqual(rows_by_user[self.user_a.user_id]["total_paid"], "120.00")
		self.assertEqual(rows_by_user[self.user_a.user_id]["total_owed"], "60.00")
		self.assertEqual(rows_by_user[self.user_a.user_id]["settlement_received"], "15.00")
		self.assertEqual(rows_by_user[self.user_a.user_id]["net_balance"], "75.00")
		self.assertEqual(rows_by_user[self.user_a.user_id]["status"], "gets_back")

		self.assertEqual(rows_by_user[self.user_b.user_id]["net_balance"], "0.00")
		self.assertEqual(rows_by_user[self.user_b.user_id]["status"], "settled")

		self.assertEqual(rows_by_user[self.user_c.user_id]["settlement_sent"], "15.00")
		self.assertEqual(rows_by_user[self.user_c.user_id]["net_balance"], "-75.00")
		self.assertEqual(rows_by_user[self.user_c.user_id]["status"], "owes")

	def test_group_pairwise_balances_reflect_expenses_and_settlements(self):
		self.client.force_authenticate(user=self.user_a)

		response = self.client.get(self.group_pairwise_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["count"], 3)

		rows = {
			(row["from_user"]["user_id"], row["to_user"]["user_id"]): row["amount"]
			for row in response.data["results"]
		}
		self.assertEqual(rows[(self.user_b.user_id, self.user_a.user_id)], "20.00")
		self.assertEqual(rows[(self.user_c.user_id, self.user_a.user_id)], "25.00")
		self.assertEqual(rows[(self.user_c.user_id, self.user_b.user_id)], "20.00")

	def test_my_balances_returns_group_rows_and_totals(self):
		self.client.force_authenticate(user=self.user_a)

		response = self.client.get(self.my_balances_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["user"]["user_id"], self.user_a.user_id)
		self.assertEqual(response.data["count"], 1)
		self.assertEqual(response.data["results"][0]["group_id"], self.group.group_id)
		self.assertEqual(response.data["results"][0]["net_balance"], "75.00")
		self.assertEqual(response.data["totals"]["net_balance"], "75.00")

	def test_non_member_cannot_access_group_balance_endpoints(self):
		self.client.force_authenticate(user=self.stranger)

		balances_response = self.client.get(self.group_balances_url)
		pairwise_response = self.client.get(self.group_pairwise_url)

		self.assertEqual(balances_response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertEqual(pairwise_response.status_code, status.HTTP_403_FORBIDDEN)
