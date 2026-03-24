from django.contrib import admin

from .models import Group, GroupMember


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
	list_display = ("group_id", "group_name", "created_by", "created_at")
	search_fields = ("group_name", "created_by__email", "created_by__name")
	list_filter = ("created_at",)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
	list_display = ("group_member_id", "group", "user", "joined_at")
	search_fields = ("group__group_name", "user__email", "user__name")
	list_filter = ("joined_at",)

# Register your models here.
