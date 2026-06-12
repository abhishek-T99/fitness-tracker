from django.contrib import admin

from .models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "primary_muscle", "equipment", "is_compound")
    list_filter = ("category", "primary_muscle", "equipment", "is_compound")
    search_fields = ("name", "instructions")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("category", "name")
    fieldsets = (
        (None, {"fields": ("name", "slug", "is_compound")}),
        ("Classification", {
            "fields": ("category", "primary_muscle", "secondary_muscles", "equipment"),
        }),
        ("Instructions", {"fields": ("instructions",), "classes": ("collapse",)}),
    )
