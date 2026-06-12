from django.contrib import admin

from .models import Food, Meal, MealItem, WaterLog


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = (
        "name", "brand", "calories", "protein_g",
        "carbs_g", "fat_g", "is_public",
    )
    list_filter = ("is_public",)
    search_fields = ("name", "brand")
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "brand", "is_public", "created_by")}),
        ("Macros (per 100 g)", {
            "fields": ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g"),
        }),
    )


class MealItemInline(admin.TabularInline):
    model = MealItem
    extra = 0
    fields = ("food", "servings")
    autocomplete_fields = ("food",)


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("user", "meal_type", "consumed_at", "item_count")
    list_filter = ("meal_type",)
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
    date_hierarchy = "consumed_at"
    ordering = ("-consumed_at",)
    inlines = [MealItemInline]

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()


@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_ml", "logged_at")
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
    date_hierarchy = "logged_at"
    ordering = ("-logged_at",)
