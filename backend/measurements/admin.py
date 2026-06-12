from django.contrib import admin

from .models import BodyMeasurement


@admin.register(BodyMeasurement)
class BodyMeasurementAdmin(admin.ModelAdmin):
    list_display = ("user", "recorded_at", "weight_kg", "body_fat_percent")
    list_filter = ("recorded_at",)
    search_fields = ("user__username",)
