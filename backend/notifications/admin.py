from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ["recipient", "notif_type", "actor", "read", "created_at"]
    list_filter   = ["notif_type", "read"]
    search_fields = ["recipient__username", "message"]
    readonly_fields = ["created_at"]
    ordering = ["read", "-created_at"]
