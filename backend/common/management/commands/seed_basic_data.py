from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from expenses.models import Expense, ExpenseSplit
from groups_app.models import Group, GroupMember
from settlements.models import Settlement


class Command(BaseCommand):
    help = "Seed basic demo data for SplitRight"

    def handle(self, *args, **options):
        user_model = get_user_model()

        alice, _ = user_model.objects.get_or_create(
            email="alice@example.com",
            defaults={"name": "Alice"},
        )
        if not alice.has_usable_password():
            alice.set_password("Password123!")
            alice.save(update_fields=["password"])

        bob, _ = user_model.objects.get_or_create(
            email="bob@example.com",
            defaults={"name": "Bob"},
        )
        if not bob.has_usable_password():
            bob.set_password("Password123!")
            bob.save(update_fields=["password"])

        carol, _ = user_model.objects.get_or_create(
            email="carol@example.com",
            defaults={"name": "Carol"},
        )
        if not carol.has_usable_password():
            carol.set_password("Password123!")
            carol.save(update_fields=["password"])

        trip, _ = Group.objects.get_or_create(
            group_name="Goa Trip",
            created_by=alice,
        )

        for user in [alice, bob, carol]:
            GroupMember.objects.get_or_create(group=trip, user=user)

        dinner, created = Expense.objects.get_or_create(
            group=trip,
            paid_by=alice,
            amount=Decimal("1500.00"),
            expense_date=date.today(),
            description="Dinner",
        )

        if created:
            ExpenseSplit.objects.create(expense=dinner, user=alice, share_amount=Decimal("500.00"))
            ExpenseSplit.objects.create(expense=dinner, user=bob, share_amount=Decimal("500.00"))
            ExpenseSplit.objects.create(expense=dinner, user=carol, share_amount=Decimal("500.00"))

        Settlement.objects.get_or_create(
            group=trip,
            from_user=bob,
            to_user=alice,
            amount=Decimal("200.00"),
            settlement_date=date.today(),
        )

        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully."))
