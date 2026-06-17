from django.contrib import admin

from .models import UserLevel, UserWeeklyChallenge, WeeklyChallenge, XPTransaction


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ["user", "level", "tier", "athlete_class", "total_xp", "prestige_count", "updated_at"]
    list_filter  = ["tier", "athlete_class"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["total_xp", "level", "tier", "updated_at"]


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display  = ["user", "amount", "base_amount", "multiplier", "source_type", "reason", "created_at"]
    list_filter   = ["source_type"]
    search_fields = ["user__username", "reason"]
    readonly_fields = ["created_at"]


@admin.register(WeeklyChallenge)
class WeeklyChallengeAdmin(admin.ModelAdmin):
    list_display = ["week_start", "challenge_type", "description", "target_value", "xp_reward"]
    list_filter  = ["challenge_type"]


@admin.register(UserWeeklyChallenge)
class UserWeeklyChallengeAdmin(admin.ModelAdmin):
    list_display = ["user", "challenge", "current_value", "completed", "completed_at"]
    list_filter  = ["completed"]
    search_fields = ["user__username"]
