from django.contrib import admin

from .models import Achievement, Streak, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "threshold")
    list_filter = ("kind",)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "unlocked_at")


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ("user", "current_days", "longest_days", "last_workout_date")
