from django.contrib import admin
from django.utils.html import format_html

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        "title", "user", "type_badge", "time_of_day",
        "days_summary", "active_badge",
    )
    list_filter = ("reminder_type", "is_active")
    search_fields = ("title", "user__username")
    autocomplete_fields = ("user",)
    ordering = ("time_of_day",)
    fieldsets = (
        (None, {"fields": ("user", "title", "reminder_type", "is_active")}),
        ("Schedule", {"fields": ("time_of_day", "days_of_week")}),
    )

    @admin.display(description="Type")
    def type_badge(self, obj):
        colours = {
            "workout": "#0ea5e9",
            "nutrition": "#10b981",
            "water": "#06b6d4",
            "custom": "#8b5cf6",
        }
        colour = colours.get(obj.reminder_type, "#94a3b8")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:11px;font-weight:600;">{}</span>',
            colour, obj.get_reminder_type_display(),
        )

    @admin.display(description="Days")
    def days_summary(self, obj):
        days = obj.days_of_week or []
        if not days:
            return "Every day"
        return ", ".join(d.capitalize() for d in days)

    @admin.display(description="Active")
    def active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#10b981;font-weight:700;">● Active</span>'
            )
        return format_html(
            '<span style="color:#94a3b8;">○ Paused</span>'
        )
