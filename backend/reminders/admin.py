from django.contrib import admin

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "reminder_type", "time_of_day", "is_active")
    list_filter = ("reminder_type", "is_active")
