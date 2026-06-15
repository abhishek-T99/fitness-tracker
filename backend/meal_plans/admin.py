from django.contrib import admin

from .models import MealPlan, MealPlanItem


class MealPlanItemInline(admin.TabularInline):
    model  = MealPlanItem
    extra  = 0
    fields = ["day", "meal_type", "food", "servings", "order"]


@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display  = ["user", "name", "week_start", "created_at"]
    list_filter   = ["week_start"]
    search_fields = ["user__username", "name"]
    inlines       = [MealPlanItemInline]
