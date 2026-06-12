from django.conf import settings
from django.db import models


class Food(models.Model):
    name = models.CharField(max_length=120)
    brand = models.CharField(max_length=80, blank=True)
    serving_size = models.DecimalField(max_digits=7, decimal_places=2, default=100)
    serving_unit = models.CharField(max_length=20, default="g")
    calories = models.DecimalField(max_digits=7, decimal_places=2)
    protein_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carbs_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fat_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fiber_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sugar_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="foods_created",
    )
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class Meal(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        DINNER = "dinner", "Dinner"
        SNACK = "snack", "Snack"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meals")
    meal_type = models.CharField(max_length=20, choices=MealType.choices)
    consumed_at = models.DateTimeField()
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-consumed_at"]

    @property
    def totals(self):
        out = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
        for item in self.items.all():
            out["calories"] += float(item.calories)
            out["protein_g"] += float(item.protein_g)
            out["carbs_g"] += float(item.carbs_g)
            out["fat_g"] += float(item.fat_g)
        return {k: round(v, 1) for k, v in out.items()}


class MealItem(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="items")
    food = models.ForeignKey(Food, on_delete=models.PROTECT)
    servings = models.DecimalField(max_digits=6, decimal_places=2, default=1)

    @property
    def _factor(self):
        return float(self.servings)

    @property
    def calories(self):
        return round(float(self.food.calories) * self._factor, 1)

    @property
    def protein_g(self):
        return round(float(self.food.protein_g) * self._factor, 1)

    @property
    def carbs_g(self):
        return round(float(self.food.carbs_g) * self._factor, 1)

    @property
    def fat_g(self):
        return round(float(self.food.fat_g) * self._factor, 1)


class WaterLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="water_logs")
    amount_ml = models.PositiveIntegerField()
    logged_at = models.DateTimeField()

    class Meta:
        ordering = ["-logged_at"]
