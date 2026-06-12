from django.contrib import admin
from django.utils.html import format_html

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = (
        "title", "user", "goal_type", "status_badge",
        "progress_bar", "deadline",
    )
    list_filter = ("status", "goal_type")
    search_fields = ("title", "user__username")
    autocomplete_fields = ("user",)
    date_hierarchy = "deadline"
    ordering = ("deadline",)
    fieldsets = (
        (None, {"fields": ("user", "title", "goal_type", "status")}),
        ("Progress", {"fields": ("target_value", "current_value", "unit")}),
        ("Timeline", {"fields": ("deadline", "notes")}),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            "active": ("#0ea5e9", "#fff"),
            "achieved": ("#10b981", "#fff"),
            "abandoned": ("#94a3b8", "#fff"),
        }
        bg, fg = colours.get(obj.status, ("#94a3b8", "#fff"))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;'
            'border-radius:9999px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display(),
        )

    @admin.display(description="Progress")
    def progress_bar(self, obj):
        if not obj.target_value or obj.target_value == 0:
            return "—"
        pct = min(int((obj.current_value or 0) / obj.target_value * 100), 100)
        colour = "#10b981" if pct >= 100 else "#0ea5e9"
        return format_html(
            '<div style="width:120px;background:#1e293b;border-radius:9999px;height:8px;">'
            '<div style="width:{pct}%;background:{colour};height:8px;border-radius:9999px;"></div>'
            '</div><span style="font-size:11px;color:#94a3b8;margin-left:6px;">{pct}%</span>',
            pct=pct, colour=colour,
        )
