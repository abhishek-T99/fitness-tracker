from django.contrib import admin

from .models import BodyMeasurement


@admin.register(BodyMeasurement)
class BodyMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "user", "recorded_at", "weight_kg", "body_fat_percent",
        "waist_cm", "chest_cm",
    )
    list_filter = ("recorded_at",)
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
    date_hierarchy = "recorded_at"
    ordering = ("-recorded_at",)
    fieldsets = (
        (None, {"fields": ("user", "recorded_at")}),
        ("Body composition", {"fields": ("weight_kg", "body_fat_percent")}),
        ("Circumference (cm)", {
            "fields": ("waist_cm", "chest_cm", "hips_cm", "thigh_cm", "arm_cm"),
            "classes": ("collapse",),
        }),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )
