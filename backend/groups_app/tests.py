from rest_framework import status
from rest_framework.test import APITestCase
from django.db import IntegrityError

from accounts.models import User

from .models import Group, GroupMember


class GroupApiTests(APITestCase):
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
		self.stranger = User.objects.create_user(
			email="stranger@example.com",
			name="Stranger",
			password="pass12345",
		)

		self.group = Group.objects.create(group_name="Trip", created_by=self.owner)
		GroupMember.objects.create(group=self.group, user=self.owner)

	def test_create_group_auto_adds_creator_as_member(self):
		self.client.force_authenticate(user=self.member)

		response = self.client.post("/api/groups", {"group_name": "Dinner Club"}, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		group_id = response.data["group"]["group_id"]
		self.assertTrue(
			GroupMember.objects.filter(group_id=group_id, user=self.member).exists()
		)

	def test_list_groups_returns_only_memberships(self):
		other_group = Group.objects.create(group_name="Office", created_by=self.member)
		GroupMember.objects.create(group=other_group, user=self.member)

		self.client.force_authenticate(user=self.owner)
		response = self.client.get("/api/groups")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		returned_ids = {group["group_id"] for group in response.data["results"]}
		self.assertEqual(returned_ids, {self.group.group_id})

	def test_join_group_success(self):
		self.client.force_authenticate(user=self.member)

		response = self.client.post(f"/api/groups/{self.group.group_id}/join", {}, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(
			GroupMember.objects.filter(group=self.group, user=self.member).exists()
		)

	def test_join_group_duplicate_is_blocked(self):
		GroupMember.objects.create(group=self.group, user=self.member)
		self.client.force_authenticate(user=self.member)

		response = self.client.post(f"/api/groups/{self.group.group_id}/join", {}, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_group_detail_blocks_non_member(self):
		self.client.force_authenticate(user=self.stranger)

		response = self.client.get(f"/api/groups/{self.group.group_id}")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_group_detail_allows_member(self):
		self.client.force_authenticate(user=self.owner)

		response = self.client.get(f"/api/groups/{self.group.group_id}")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["group_id"], self.group.group_id)

	def test_group_members_blocks_non_member(self):
		self.client.force_authenticate(user=self.stranger)

		response = self.client.get(f"/api/groups/{self.group.group_id}/members")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_group_members_lists_members_for_member(self):
		GroupMember.objects.create(group=self.group, user=self.member)
		self.client.force_authenticate(user=self.owner)

		response = self.client.get(f"/api/groups/{self.group.group_id}/members")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["count"], 2)
		returned_user_ids = {entry["user"]["user_id"] for entry in response.data["results"]}
		self.assertEqual(returned_user_ids, {self.owner.user_id, self.member.user_id})

	def test_group_member_unique_constraint_enforced(self):
		with self.assertRaises(IntegrityError):
			GroupMember.objects.create(group=self.group, user=self.owner)
