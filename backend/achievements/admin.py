from django.contrib import admin
from django.utils.html import format_html

from .models import Achievement, Streak, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "kind_badge", "threshold", "unlock_count")
    list_filter = ("kind",)
    search_fields = ("name", "description")
    ordering = ("kind", "threshold")
    fieldsets = (
        (None, {"fields": ("name", "kind", "threshold")}),
        ("Details", {"fields": ("description", "icon")}),
    )

    @admin.display(description="Kind")
    def kind_badge(self, obj):
        colours = {
            "workout_count": "#0ea5e9",
            "total_volume": "#8b5cf6",
            "streak": "#f59e0b",
            "weight_loss": "#10b981",
        }
        colour = colours.get(obj.kind, "#94a3b8")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:9999px;font-size:11px;font-weight:600;">{}</span>',
            colour, obj.get_kind_display(),
        )

    @admin.display(description="Unlocked by")
    def unlock_count(self, obj):
        return obj.userachievement_set.count()


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "unlocked_at")
    list_filter = ("achievement__kind",)
    search_fields = ("user__username", "achievement__name")
    autocomplete_fields = ("user",)
    date_hierarchy = "unlocked_at"
    ordering = ("-unlocked_at",)


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = (
        "user", "current_days_display", "longest_days",
        "last_workout_date",
    )
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
    ordering = ("-current_days",)
    readonly_fields = ("current_days", "longest_days", "last_workout_date")

    @admin.display(description="Current streak")
    def current_days_display(self, obj):
        if obj.current_days >= 7:
            colour = "#f59e0b"
        elif obj.current_days > 0:
            colour = "#0ea5e9"
        else:
            colour = "#94a3b8"
        return format_html(
            '<span style="color:{};font-weight:700;">{} days</span>',
            colour, obj.current_days,
        )
