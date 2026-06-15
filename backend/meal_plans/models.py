from django.conf import settings
from django.db import models


MEAL_TYPES = [
    ("breakfast", "Breakfast"),
    ("lunch",     "Lunch"),
    ("dinner",    "Dinner"),
    ("snack",     "Snack"),
]

DAY_CHOICES = [
    (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
    (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
]


class MealPlan(models.Model):
    """Week-scoped meal plan. week_start is always the Monday of that week."""

    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meal_plans"
    )
    name       = models.CharField(max_length=120, default="My meal plan")
    week_start = models.DateField(help_text="Always the Monday of the target week.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-week_start"]

    def __str__(self):
        return f"{self.user.username} / {self.week_start} / {self.name}"


class MealPlanItem(models.Model):
    """One food entry in a plan slot (day × meal_type)."""

    plan      = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name="items")
    day       = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    food      = models.ForeignKey("nutrition.Food", on_delete=models.PROTECT)
    servings  = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    order     = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["day", "meal_type", "order"]

    @property
    def calories(self):
        return round(float(self.food.calories) * float(self.servings), 1)

    @property
    def protein_g(self):
        return round(float(self.food.protein_g) * float(self.servings), 1)

    @property
    def carbs_g(self):
        return round(float(self.food.carbs_g) * float(self.servings), 1)

    @property
    def fat_g(self):
        return round(float(self.food.fat_g) * float(self.servings), 1)

    def __str__(self):
        return f"Day{self.day} {self.meal_type} / {self.food.name}"
