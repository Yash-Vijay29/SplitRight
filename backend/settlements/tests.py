from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from groups_app.models import Group, GroupMember

from .models import Settlement


class SettlementApiTests(APITestCase):
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

		self.url = f"/api/groups/{self.group.group_id}/settlements"

	def test_create_settlement_success(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"from_user": self.member.user_id,
			"to_user": self.owner.user_id,
			"amount": "45.50",
			"settlement_date": str(date.today()),
		}

		response = self.client.post(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Settlement.objects.count(), 1)
		settlement = Settlement.objects.first()
		self.assertEqual(settlement.from_user_id, self.member.user_id)
		self.assertEqual(settlement.to_user_id, self.owner.user_id)
		self.assertEqual(settlement.amount, Decimal("45.50"))

	def test_create_settlement_rejects_self_payment(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"from_user": self.owner.user_id,
			"to_user": self.owner.user_id,
			"amount": "30.00",
			"settlement_date": str(date.today()),
		}

		response = self.client.post(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("to_user", response.data)
		self.assertEqual(Settlement.objects.count(), 0)

	def test_create_settlement_rejects_non_member_users(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"from_user": self.stranger.user_id,
			"to_user": self.owner.user_id,
			"amount": "25.00",
			"settlement_date": str(date.today()),
		}

		response = self.client.post(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("from_user", response.data)
		self.assertEqual(Settlement.objects.count(), 0)

	def test_create_settlement_rejects_non_positive_amount(self):
		self.client.force_authenticate(user=self.owner)
		payload = {
			"from_user": self.member.user_id,
			"to_user": self.owner.user_id,
			"amount": "0.00",
			"settlement_date": str(date.today()),
		}

		response = self.client.post(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("amount", response.data)
		self.assertEqual(Settlement.objects.count(), 0)

	def test_list_settlements_returns_group_history(self):
		self.client.force_authenticate(user=self.owner)
		Settlement.objects.create(
			group=self.group,
			from_user=self.member,
			to_user=self.owner,
			amount=Decimal("10.00"),
			settlement_date=date.today(),
		)
		Settlement.objects.create(
			group=self.group,
			from_user=self.owner,
			to_user=self.member,
			amount=Decimal("5.00"),
			settlement_date=date.today(),
		)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["count"], 2)
		self.assertEqual(len(response.data["results"]), 2)

	def test_non_member_cannot_list_or_create_settlements(self):
		self.client.force_authenticate(user=self.stranger)

		list_response = self.client.get(self.url)
		self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)

		payload = {
			"from_user": self.member.user_id,
			"to_user": self.owner.user_id,
			"amount": "50.00",
			"settlement_date": str(date.today()),
		}
		create_response = self.client.post(self.url, payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

	def test_list_returns_only_target_group_settlements(self):
		other_group = Group.objects.create(group_name="Office", created_by=self.owner)
		GroupMember.objects.create(group=other_group, user=self.owner)
		GroupMember.objects.create(group=other_group, user=self.member_two)

		Settlement.objects.create(
			group=self.group,
			from_user=self.member,
			to_user=self.owner,
			amount=Decimal("15.00"),
			settlement_date=date.today(),
		)
		Settlement.objects.create(
			group=other_group,
			from_user=self.member_two,
			to_user=self.owner,
			amount=Decimal("33.00"),
			settlement_date=date.today(),
		)

		self.client.force_authenticate(user=self.owner)
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["count"], 1)
		self.assertEqual(
			response.data["results"][0]["amount"],
			"15.00",
		)

	def test_settlement_model_rejects_same_from_and_to_user(self):
		with self.assertRaises(ValidationError):
			Settlement.objects.create(
				group=self.group,
				from_user=self.owner,
				to_user=self.owner,
				amount=Decimal("10.00"),
				settlement_date=date.today(),
			)
