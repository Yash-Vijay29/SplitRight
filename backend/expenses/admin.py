from django.contrib import admin

from .models import Expense, ExpenseSplit


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
	list_display = ("expense_id", "group", "paid_by", "amount", "expense_date", "created_at")
	search_fields = ("group__group_name", "paid_by__email", "description")
	list_filter = ("expense_date", "created_at")


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
	list_display = ("expense_split_id", "expense", "user", "share_amount")
	search_fields = ("expense__group__group_name", "user__email", "user__name")

# Register your models here.
