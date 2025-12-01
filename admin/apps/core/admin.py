from django.contrib import admin
from unfold.admin import ModelAdmin

from admin.apps.core.models import AdminSettings, ActivityLog


@admin.register(AdminSettings)
class AdminSettingsAdmin(ModelAdmin):
    list_display = ["key", "description", "updated_at", "updated_by"]
    search_fields = ["key", "description"]
    readonly_fields = ["updated_at"]


@admin.register(ActivityLog)
class ActivityLogAdmin(ModelAdmin):
    list_display = ["action", "user", "description", "ip_address", "created_at"]
    list_filter = ["action", "user", "created_at"]
    search_fields = ["description", "user__username"]
    readonly_fields = ["user", "action", "description", "metadata", "ip_address", "user_agent", "created_at"]
    date_hierarchy = "created_at"
