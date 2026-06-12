from django.core.management.base import BaseCommand

from nutrition.models import Food

FOODS = [
    {"name": "Chicken Breast (cooked)", "serving_size": 100, "serving_unit": "g",
     "calories": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6},
    {"name": "Brown Rice (cooked)", "serving_size": 100, "serving_unit": "g",
     "calories": 112, "protein_g": 2.6, "carbs_g": 24, "fat_g": 0.9, "fiber_g": 1.8},
    {"name": "White Rice (cooked)", "serving_size": 100, "serving_unit": "g",
     "calories": 130, "protein_g": 2.7, "carbs_g": 28, "fat_g": 0.3},
    {"name": "Egg, large", "serving_size": 50, "serving_unit": "g",
     "calories": 72, "protein_g": 6.3, "carbs_g": 0.4, "fat_g": 4.8},
    {"name": "Oats (dry)", "serving_size": 40, "serving_unit": "g",
     "calories": 150, "protein_g": 5, "carbs_g": 27, "fat_g": 2.5, "fiber_g": 4},
    {"name": "Banana", "serving_size": 118, "serving_unit": "g",
     "calories": 105, "protein_g": 1.3, "carbs_g": 27, "fat_g": 0.4, "fiber_g": 3.1, "sugar_g": 14},
    {"name": "Apple", "serving_size": 182, "serving_unit": "g",
     "calories": 95, "protein_g": 0.5, "carbs_g": 25, "fat_g": 0.3, "fiber_g": 4.4, "sugar_g": 19},
    {"name": "Greek Yogurt (plain, non-fat)", "serving_size": 170, "serving_unit": "g",
     "calories": 100, "protein_g": 17, "carbs_g": 6, "fat_g": 0.7},
    {"name": "Whole Milk", "serving_size": 240, "serving_unit": "ml",
     "calories": 149, "protein_g": 7.7, "carbs_g": 12, "fat_g": 8},
    {"name": "Almonds", "serving_size": 28, "serving_unit": "g",
     "calories": 164, "protein_g": 6, "carbs_g": 6, "fat_g": 14, "fiber_g": 3.5},
    {"name": "Peanut Butter", "serving_size": 32, "serving_unit": "g",
     "calories": 188, "protein_g": 8, "carbs_g": 7, "fat_g": 16, "fiber_g": 2},
    {"name": "Avocado", "serving_size": 150, "serving_unit": "g",
     "calories": 240, "protein_g": 3, "carbs_g": 13, "fat_g": 22, "fiber_g": 10},
    {"name": "Broccoli (cooked)", "serving_size": 100, "serving_unit": "g",
     "calories": 35, "protein_g": 2.4, "carbs_g": 7.2, "fat_g": 0.4, "fiber_g": 3.3},
    {"name": "Sweet Potato (baked)", "serving_size": 100, "serving_unit": "g",
     "calories": 90, "protein_g": 2, "carbs_g": 21, "fat_g": 0.1, "fiber_g": 3.3},
    {"name": "Whole Wheat Bread", "serving_size": 28, "serving_unit": "g",
     "calories": 70, "protein_g": 3.6, "carbs_g": 13, "fat_g": 1, "fiber_g": 2},
    {"name": "Salmon (cooked)", "serving_size": 100, "serving_unit": "g",
     "calories": 208, "protein_g": 22, "carbs_g": 0, "fat_g": 13},
    {"name": "Ground Beef 90/10 (cooked)", "serving_size": 100, "serving_unit": "g",
     "calories": 217, "protein_g": 26, "carbs_g": 0, "fat_g": 12},
    {"name": "Tofu (firm)", "serving_size": 100, "serving_unit": "g",
     "calories": 144, "protein_g": 17, "carbs_g": 3, "fat_g": 9},
    {"name": "Lentils (cooked)", "serving_size": 100, "serving_unit": "g",
     "calories": 116, "protein_g": 9, "carbs_g": 20, "fat_g": 0.4, "fiber_g": 8},
    {"name": "Whey Protein Powder", "serving_size": 30, "serving_unit": "g",
     "calories": 120, "protein_g": 24, "carbs_g": 3, "fat_g": 1.5},
]


class Command(BaseCommand):
    help = "Seed the database with a starter food library."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for payload in FOODS:
            obj, was_created = Food.objects.update_or_create(
                name=payload["name"], brand="", defaults=payload
            )
            created += int(was_created)
            updated += int(not was_created)
        self.stdout.write(self.style.SUCCESS(
            f"Seeded foods: {created} created, {updated} updated."
        ))
