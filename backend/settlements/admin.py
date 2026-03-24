from django.contrib import admin

from .models import Settlement


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
	list_display = (
		"settlement_id",
		"group",
		"from_user",
		"to_user",
		"amount",
		"settlement_date",
		"created_at",
	)
	search_fields = ("group__group_name", "from_user__email", "to_user__email")
	list_filter = ("settlement_date", "created_at")

# Register your models here.
