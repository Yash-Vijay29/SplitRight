from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from groups_app.models import Group, GroupMember

from .models import Expense, ExpenseSplit


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
