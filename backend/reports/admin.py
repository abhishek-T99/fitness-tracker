from django.contrib import admin

from .models import FitnessReport


@admin.register(FitnessReport)
class FitnessReportAdmin(admin.ModelAdmin):
    list_display = ("user", "period_type", "period_start", "period_end", "generated_at", "emailed_at")
    list_filter = ("period_type",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("generated_at",)
    date_hierarchy = "generated_at"
