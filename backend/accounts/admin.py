from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	model = User
	list_display = ("user_id", "email", "name", "is_staff", "is_active", "created_at")
	ordering = ("-created_at",)
	search_fields = ("email", "name")
	readonly_fields = ("created_at",)

	fieldsets = (
		(None, {"fields": ("email", "password")}),
		("Profile", {"fields": ("name",)}),
		(
			"Permissions",
			{
				"fields": (
					"is_active",
					"is_staff",
					"is_superuser",
					"groups",
					"user_permissions",
				)
			},
		),
		("Timestamps", {"fields": ("created_at",)}),
	)

	add_fieldsets = (
		(
			None,
			{
				"classes": ("wide",),
				"fields": ("email", "name", "password1", "password2", "is_staff", "is_active"),
			},
		),
	)

# Register your models here.
