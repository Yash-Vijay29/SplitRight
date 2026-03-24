from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from groups_app.models import Group


class Settlement(models.Model):
	settlement_id = models.BigAutoField(primary_key=True)
	from_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="settlements_sent",
	)
	to_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="settlements_received",
	)
	group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="settlements")
	amount = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0.01"))],
	)
	settlement_date = models.DateField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "settlements"
		ordering = ["-settlement_date", "-created_at"]
		indexes = [
			models.Index(fields=["group"], name="idx_settlement_group"),
			models.Index(fields=["from_user"], name="idx_settlement_from_user"),
			models.Index(fields=["to_user"], name="idx_settlement_to_user"),
		]
		constraints = [
			models.CheckConstraint(check=models.Q(amount__gt=0), name="chk_settlement_amount_gt_zero"),
			models.CheckConstraint(check=~models.Q(from_user=models.F("to_user")), name="chk_settlement_users_distinct"),
		]

	def clean(self):
		super().clean()
		if self.from_user_id == self.to_user_id:
			raise ValidationError({"to_user": "from_user and to_user must be different."})

		from_member = self.group.memberships.filter(user_id=self.from_user_id).exists()
		to_member = self.group.memberships.filter(user_id=self.to_user_id).exists()

		if not from_member:
			raise ValidationError({"from_user": "from_user must be a member of the group."})
		if not to_member:
			raise ValidationError({"to_user": "to_user must be a member of the group."})

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)

	def __str__(self):
		return f"Settlement {self.from_user_id} -> {self.to_user_id}"
