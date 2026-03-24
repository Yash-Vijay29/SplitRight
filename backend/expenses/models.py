from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from groups_app.models import Group


class Expense(models.Model):
	expense_id = models.BigAutoField(primary_key=True)
	group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="expenses")
	paid_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="expenses_paid",
	)
	amount = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0.01"))],
	)
	expense_date = models.DateField()
	description = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "expenses"
		ordering = ["-expense_date", "-created_at"]
		indexes = [
			models.Index(fields=["group"], name="idx_expense_group"),
			models.Index(fields=["paid_by"], name="idx_expense_paid_by"),
		]
		constraints = [
			models.CheckConstraint(check=models.Q(amount__gt=0), name="chk_expense_amount_gt_zero"),
		]

	def clean(self):
		super().clean()
		payer_is_member = self.group.memberships.filter(user_id=self.paid_by_id).exists()
		if not payer_is_member:
			raise ValidationError({"paid_by": "Payer must be a member of the group."})

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)

	def __str__(self):
		return f"Expense {self.expense_id} in group {self.group_id}"


class ExpenseSplit(models.Model):
	expense_split_id = models.BigAutoField(primary_key=True)
	expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="splits")
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="expense_splits",
	)
	share_amount = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0"))],
	)

	class Meta:
		db_table = "expense_splits"
		constraints = [
			models.UniqueConstraint(fields=["expense", "user"], name="uq_expense_split_expense_user"),
			models.CheckConstraint(
				check=models.Q(share_amount__gte=0),
				name="chk_expense_split_share_gte_zero",
			),
		]
		indexes = [
			models.Index(fields=["user"], name="idx_expense_split_user"),
			models.Index(fields=["expense"], name="idx_expense_split_expense"),
		]

	def clean(self):
		super().clean()
		split_user_is_member = self.expense.group.memberships.filter(user_id=self.user_id).exists()
		if not split_user_is_member:
			raise ValidationError({"user": "Split user must be a member of the expense group."})

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)

	def __str__(self):
		return f"Split {self.expense_id} -> {self.user_id}"
