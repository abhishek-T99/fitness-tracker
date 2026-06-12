from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import Profile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "avatar_thumb", "username", "email", "full_name",
        "is_active", "is_staff", "date_joined",
    )
    list_display_links = ("username", "email")
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    readonly_fields = ("avatar_thumb", "date_joined", "last_login")

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile picture", {"fields": ("avatar_thumb", "avatar")}),
    )

    @admin.display(description="")
    def avatar_thumb(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="32" height="32" '
                'style="border-radius:50%;object-fit:cover;" />',
                obj.avatar.url,
            )
        initials = (obj.first_name or obj.username or "?")[0].upper()
        return format_html(
            '<span style="display:inline-flex;align-items:center;justify-content:center;'
            'width:32px;height:32px;border-radius:50%;background:#0ea5e9;'
            'color:#fff;font-weight:700;font-size:13px;">{}</span>',
            initials,
        )

    @admin.display(description="Full name")
    def full_name(self, obj):
        return obj.get_full_name() or "—"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "gender", "activity_level", "units",
        "weekly_workout_goal", "daily_calorie_goal",
    )
    list_filter = ("gender", "activity_level", "units")
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)
    readonly_fields = ("age",)
    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Personal", {"fields": ("bio", "date_of_birth", "age", "gender", "height_cm")}),
        ("Fitness", {
            "fields": ("activity_level", "units", "daily_calorie_goal", "weekly_workout_goal"),
        }),
        ("Settings", {"fields": ("timezone",)}),
    )
