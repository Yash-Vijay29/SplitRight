from django.test import TestCase
from django.core.management import call_command

from accounts.models import User
from expenses.models import Expense, ExpenseSplit
from groups_app.models import Group, GroupMember
from settlements.models import Settlement


class FrontendAppTests(TestCase):
	def test_frontend_route_returns_200(self):
		response = self.client.get("/")
		self.assertEqual(response.status_code, 200)

	def test_frontend_contains_console_title(self):
		response = self.client.get("/")
		self.assertContains(response, "Frontend Integration Console")


class SeedDemoDataCommandTests(TestCase):
	def test_seed_demo_data_creates_expected_dataset(self):
		call_command("seed_demo_data")

		self.assertTrue(Group.objects.filter(group_name="Demo Trip 2026").exists())
		group = Group.objects.get(group_name="Demo Trip 2026")

		self.assertEqual(User.objects.count(), 4)
		self.assertEqual(GroupMember.objects.filter(group=group).count(), 4)
		self.assertEqual(Expense.objects.filter(group=group).count(), 3)
		self.assertEqual(ExpenseSplit.objects.filter(expense__group=group).count(), 12)
		self.assertEqual(Settlement.objects.filter(group=group).count(), 1)

	def test_seed_demo_data_is_idempotent(self):
		call_command("seed_demo_data")
		call_command("seed_demo_data")

		group = Group.objects.get(group_name="Demo Trip 2026")
		self.assertEqual(Group.objects.filter(group_name="Demo Trip 2026").count(), 1)
		self.assertEqual(GroupMember.objects.filter(group=group).count(), 4)
		self.assertEqual(Expense.objects.filter(group=group).count(), 3)
		self.assertEqual(ExpenseSplit.objects.filter(expense__group=group).count(), 12)
		self.assertEqual(Settlement.objects.filter(group=group).count(), 1)

	def test_seed_demo_data_reset_rebuilds_clean_dataset(self):
		call_command("seed_demo_data")
		call_command("seed_demo_data", reset=True)

		group = Group.objects.get(group_name="Demo Trip 2026")
		self.assertEqual(GroupMember.objects.filter(group=group).count(), 4)
		self.assertEqual(Expense.objects.filter(group=group).count(), 3)
		self.assertEqual(ExpenseSplit.objects.filter(expense__group=group).count(), 12)
		self.assertEqual(Settlement.objects.filter(group=group).count(), 1)
