from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from expenses.models import Expense, ExpenseSplit
from groups_app.models import Group, GroupMember
from settlements.models import Settlement


class Command(BaseCommand):
    help = "Seed a reproducible demo dataset for SplitRight (Part 8)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo group data before reseeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()
        reset = options.get("reset", False)

        demo_users = [
            {"name": "Alice", "email": "alice@example.com", "password": "Password123!"},
            {"name": "Bob", "email": "bob@example.com", "password": "Password123!"},
            {"name": "Carol", "email": "carol@example.com", "password": "Password123!"},
            {"name": "Dan", "email": "dan@example.com", "password": "Password123!"},
        ]

        users_by_email = {}
        for user_data in demo_users:
            user, _ = user_model.objects.get_or_create(
                email=user_data["email"],
                defaults={"name": user_data["name"]},
            )
            user.name = user_data["name"]
            if not user.has_usable_password():
                user.set_password(user_data["password"])
            user.save(update_fields=["name", "password"])
            users_by_email[user_data["email"]] = user

        alice = users_by_email["alice@example.com"]
        bob = users_by_email["bob@example.com"]
        carol = users_by_email["carol@example.com"]
        dan = users_by_email["dan@example.com"]

        if reset:
            demo_groups = Group.objects.filter(group_name="Demo Trip 2026")
            Settlement.objects.filter(group__in=demo_groups).delete()
            ExpenseSplit.objects.filter(expense__group__in=demo_groups).delete()
            Expense.objects.filter(group__in=demo_groups).delete()
            GroupMember.objects.filter(group__in=demo_groups).delete()
            demo_groups.delete()

        group, _ = Group.objects.get_or_create(
            group_name="Demo Trip 2026",
            defaults={"created_by": alice},
        )
        if group.created_by_id != alice.user_id:
            group.created_by = alice
            group.save(update_fields=["created_by"])

        for member in [alice, bob, carol, dan]:
            GroupMember.objects.get_or_create(group=group, user=member)

        demo_expenses = [
            {
                "paid_by": alice,
                "amount": Decimal("1200.00"),
                "expense_date": date(2026, 3, 1),
                "description": "Hotel booking",
                "splits": {
                    alice: Decimal("300.00"),
                    bob: Decimal("300.00"),
                    carol: Decimal("300.00"),
                    dan: Decimal("300.00"),
                },
            },
            {
                "paid_by": bob,
                "amount": Decimal("800.00"),
                "expense_date": date(2026, 3, 2),
                "description": "Intercity cab",
                "splits": {
                    alice: Decimal("100.00"),
                    bob: Decimal("200.00"),
                    carol: Decimal("250.00"),
                    dan: Decimal("250.00"),
                },
            },
            {
                "paid_by": carol,
                "amount": Decimal("400.00"),
                "expense_date": date(2026, 3, 3),
                "description": "Dinner",
                "splits": {
                    alice: Decimal("120.00"),
                    bob: Decimal("80.00"),
                    carol: Decimal("100.00"),
                    dan: Decimal("100.00"),
                },
            },
        ]

        for expense_data in demo_expenses:
            expense, created = Expense.objects.get_or_create(
                group=group,
                paid_by=expense_data["paid_by"],
                amount=expense_data["amount"],
                expense_date=expense_data["expense_date"],
                description=expense_data["description"],
            )
            if created:
                for split_user, share_amount in expense_data["splits"].items():
                    ExpenseSplit.objects.create(
                        expense=expense,
                        user=split_user,
                        share_amount=share_amount,
                    )

        Settlement.objects.get_or_create(
            group=group,
            from_user=dan,
            to_user=alice,
            amount=Decimal("150.00"),
            settlement_date=date(2026, 3, 4),
        )

        self.stdout.write(self.style.SUCCESS("Demo dataset loaded successfully."))
        self.stdout.write(
            f"Group: {group.group_name} (group_id={group.group_id}), users: "
            "alice@example.com, bob@example.com, carol@example.com, dan@example.com"
        )
