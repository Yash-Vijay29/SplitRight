from django.conf import settings
from django.db import models


class Group(models.Model):
	group_id = models.BigAutoField(primary_key=True)
	group_name = models.CharField(max_length=150)
	is_joinable = models.BooleanField(default=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name="created_groups",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "groups"
		ordering = ["-created_at"]

	def __str__(self):
		return self.group_name


class GroupMember(models.Model):
	group_member_id = models.BigAutoField(primary_key=True)
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="group_memberships",
	)
	group = models.ForeignKey(
		Group,
		on_delete=models.CASCADE,
		related_name="memberships",
	)
	joined_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "group_members"
		constraints = [
			models.UniqueConstraint(fields=["user", "group"], name="uq_group_member_user_group"),
		]
		indexes = [
			models.Index(fields=["group"], name="idx_group_member_group"),
			models.Index(fields=["user"], name="idx_group_member_user"),
		]

	def __str__(self):
		return f"{self.user_id} in {self.group_id}"
