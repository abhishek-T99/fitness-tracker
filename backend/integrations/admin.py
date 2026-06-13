from django.contrib import admin

from .models import Integration, OAuthToken, SyncLog


class OAuthTokenInline(admin.StackedInline):
    model = OAuthToken
    extra = 0
    readonly_fields = ["expires_at", "athlete_id", "scope"]
    fields = ["athlete_id", "expires_at", "scope"]


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "is_active", "connected_at", "last_synced_at"]
    list_filter = ["provider", "is_active"]
    search_fields = ["user__username", "user__email"]
    inlines = [OAuthTokenInline]


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ["integration", "event_type", "external_id", "status", "synced_at"]
    list_filter = ["status", "event_type"]
    search_fields = ["integration__user__username", "external_id"]
    readonly_fields = ["synced_at"]
