from django.contrib import admin

from .models import Food, Meal, MealItem, WaterLog


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "calories", "protein_g", "carbs_g", "fat_g", "is_public")
    list_filter = ("is_public",)
    search_fields = ("name", "brand")


class MealItemInline(admin.TabularInline):
    model = MealItem
    extra = 0


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("user", "meal_type", "consumed_at")
    list_filter = ("meal_type",)
    inlines = [MealItemInline]


@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_ml", "logged_at")
