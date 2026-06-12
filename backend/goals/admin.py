from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "goal_type", "status", "deadline")
    list_filter = ("status", "goal_type")
    search_fields = ("title", "user__username")
