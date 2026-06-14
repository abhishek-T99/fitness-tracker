from django.core.management.base import BaseCommand

from nutrition.models import Food

# Every row: name, serving_size (number), serving_unit, calories, protein_g, carbs_g,
#            fat_g, [fiber_g], [sugar_g]
# All macros are per stated serving size. Sources: USDA FoodData Central.

FOODS = [

    # ══════════════════════════════════════════════════════════════════════════
    # PROTEINS — MEAT & FISH
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Chicken Breast (cooked)",        "serving_size": 100, "serving_unit": "g",
     "calories": 165, "protein_g": 31.0, "carbs_g":  0.0, "fat_g":  3.6},
    {"name": "Chicken Thigh (cooked, skinless)","serving_size": 100, "serving_unit": "g",
     "calories": 209, "protein_g": 25.9, "carbs_g":  0.0, "fat_g": 11.0},
    {"name": "Ground Turkey (cooked)",          "serving_size": 100, "serving_unit": "g",
     "calories": 189, "protein_g": 28.4, "carbs_g":  0.0, "fat_g":  8.3},
    {"name": "Ground Beef 90/10 (cooked)",      "serving_size": 100, "serving_unit": "g",
     "calories": 217, "protein_g": 26.1, "carbs_g":  0.0, "fat_g": 12.0},
    {"name": "Ground Beef 80/20 (cooked)",      "serving_size": 100, "serving_unit": "g",
     "calories": 254, "protein_g": 24.1, "carbs_g":  0.0, "fat_g": 17.2},
    {"name": "Beef Sirloin (cooked)",           "serving_size": 100, "serving_unit": "g",
     "calories": 207, "protein_g": 29.1, "carbs_g":  0.0, "fat_g":  9.4},
    {"name": "Salmon (cooked)",                 "serving_size": 100, "serving_unit": "g",
     "calories": 208, "protein_g": 22.0, "carbs_g":  0.0, "fat_g": 13.0},
    {"name": "Tuna (canned in water)",          "serving_size": 100, "serving_unit": "g",
     "calories":  99, "protein_g": 23.0, "carbs_g":  0.0, "fat_g":  0.5},
    {"name": "Tilapia (cooked)",                "serving_size": 100, "serving_unit": "g",
     "calories": 129, "protein_g": 26.2, "carbs_g":  0.0, "fat_g":  2.7},
    {"name": "Shrimp (cooked)",                 "serving_size": 100, "serving_unit": "g",
     "calories":  99, "protein_g": 20.9, "carbs_g":  0.9, "fat_g":  1.1},
    {"name": "Cod (cooked)",                    "serving_size": 100, "serving_unit": "g",
     "calories":  91, "protein_g": 19.4, "carbs_g":  0.0, "fat_g":  0.8},
    {"name": "Pork Tenderloin (cooked)",        "serving_size": 100, "serving_unit": "g",
     "calories": 166, "protein_g": 28.2, "carbs_g":  0.0, "fat_g":  4.6},
    {"name": "Lamb (ground, cooked)",           "serving_size": 100, "serving_unit": "g",
     "calories": 258, "protein_g": 25.4, "carbs_g":  0.0, "fat_g": 16.9},

    # ══════════════════════════════════════════════════════════════════════════
    # PROTEINS — DAIRY & EGGS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Egg, large",                      "serving_size":  50, "serving_unit": "g",
     "calories":  72, "protein_g":  6.3, "carbs_g":  0.4, "fat_g":  4.8},
    {"name": "Egg White (large)",               "serving_size":  33, "serving_unit": "g",
     "calories":  17, "protein_g":  3.6, "carbs_g":  0.2, "fat_g":  0.1},
    {"name": "Greek Yogurt (plain, non-fat)",   "serving_size": 170, "serving_unit": "g",
     "calories": 100, "protein_g": 17.0, "carbs_g":  6.0, "fat_g":  0.7},
    {"name": "Greek Yogurt (plain, full-fat)",  "serving_size": 170, "serving_unit": "g",
     "calories": 166, "protein_g": 15.0, "carbs_g":  7.0, "fat_g":  9.0},
    {"name": "Cottage Cheese (1% fat)",         "serving_size": 113, "serving_unit": "g",
     "calories":  81, "protein_g": 14.0, "carbs_g":  3.0, "fat_g":  1.1},
    {"name": "Whole Milk",                      "serving_size": 240, "serving_unit": "ml",
     "calories": 149, "protein_g":  7.7, "carbs_g": 12.0, "fat_g":  8.0,  "sugar_g": 12.0},
    {"name": "Skim Milk",                       "serving_size": 240, "serving_unit": "ml",
     "calories":  83, "protein_g":  8.3, "carbs_g": 12.2, "fat_g":  0.2,  "sugar_g": 12.5},
    {"name": "Cheddar Cheese",                  "serving_size":  28, "serving_unit": "g",
     "calories": 113, "protein_g":  7.0, "carbs_g":  0.4, "fat_g":  9.3},
    {"name": "Mozzarella (part-skim)",          "serving_size":  28, "serving_unit": "g",
     "calories":  72, "protein_g":  6.9, "carbs_g":  0.9, "fat_g":  4.5},
    {"name": "Whey Protein Powder",             "serving_size":  30, "serving_unit": "g",
     "calories": 120, "protein_g": 24.0, "carbs_g":  3.0, "fat_g":  1.5},
    {"name": "Casein Protein Powder",           "serving_size":  33, "serving_unit": "g",
     "calories": 120, "protein_g": 24.0, "carbs_g":  4.0, "fat_g":  1.0},

    # ══════════════════════════════════════════════════════════════════════════
    # PROTEINS — PLANT-BASED
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Tofu (firm)",                     "serving_size": 100, "serving_unit": "g",
     "calories": 144, "protein_g": 17.0, "carbs_g":  3.0, "fat_g":  9.0},
    {"name": "Tempeh",                          "serving_size": 100, "serving_unit": "g",
     "calories": 193, "protein_g": 20.3, "carbs_g":  9.4, "fat_g": 10.8, "fiber_g": 0.0},
    {"name": "Edamame (cooked)",                "serving_size": 100, "serving_unit": "g",
     "calories": 121, "protein_g": 11.9, "carbs_g":  8.9, "fat_g":  5.2, "fiber_g": 5.2},
    {"name": "Lentils (cooked)",                "serving_size": 100, "serving_unit": "g",
     "calories": 116, "protein_g":  9.0, "carbs_g": 20.0, "fat_g":  0.4, "fiber_g": 7.9},
    {"name": "Chickpeas (cooked)",              "serving_size": 100, "serving_unit": "g",
     "calories": 164, "protein_g":  8.9, "carbs_g": 27.4, "fat_g":  2.6, "fiber_g": 7.6},
    {"name": "Black Beans (cooked)",            "serving_size": 100, "serving_unit": "g",
     "calories": 132, "protein_g":  8.9, "carbs_g": 23.7, "fat_g":  0.5, "fiber_g": 8.7},
    {"name": "Kidney Beans (cooked)",           "serving_size": 100, "serving_unit": "g",
     "calories": 127, "protein_g":  8.7, "carbs_g": 22.8, "fat_g":  0.5, "fiber_g": 6.4},
    {"name": "Pea Protein Powder",              "serving_size":  30, "serving_unit": "g",
     "calories": 110, "protein_g": 22.0, "carbs_g":  2.0, "fat_g":  1.0},

    # ══════════════════════════════════════════════════════════════════════════
    # CARBOHYDRATES — GRAINS & STARCHES
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "White Rice (cooked)",             "serving_size": 100, "serving_unit": "g",
     "calories": 130, "protein_g":  2.7, "carbs_g": 28.0, "fat_g":  0.3},
    {"name": "Brown Rice (cooked)",             "serving_size": 100, "serving_unit": "g",
     "calories": 112, "protein_g":  2.6, "carbs_g": 24.0, "fat_g":  0.9, "fiber_g": 1.8},
    {"name": "Jasmine Rice (cooked)",           "serving_size": 100, "serving_unit": "g",
     "calories": 129, "protein_g":  2.5, "carbs_g": 28.3, "fat_g":  0.2},
    {"name": "Oats (dry)",                      "serving_size":  40, "serving_unit": "g",
     "calories": 150, "protein_g":  5.0, "carbs_g": 27.0, "fat_g":  2.5, "fiber_g": 4.0},
    {"name": "Pasta (cooked)",                  "serving_size": 100, "serving_unit": "g",
     "calories": 131, "protein_g":  5.0, "carbs_g": 25.0, "fat_g":  1.1, "fiber_g": 1.8},
    {"name": "Whole Wheat Pasta (cooked)",      "serving_size": 100, "serving_unit": "g",
     "calories": 124, "protein_g":  5.3, "carbs_g": 26.5, "fat_g":  0.5, "fiber_g": 3.9},
    {"name": "Whole Wheat Bread",               "serving_size":  28, "serving_unit": "g",
     "calories":  70, "protein_g":  3.6, "carbs_g": 13.0, "fat_g":  1.0, "fiber_g": 2.0},
    {"name": "White Bread",                     "serving_size":  25, "serving_unit": "g",
     "calories":  67, "protein_g":  2.1, "carbs_g": 12.6, "fat_g":  0.9},
    {"name": "Sourdough Bread",                 "serving_size":  56, "serving_unit": "g",
     "calories": 148, "protein_g":  5.8, "carbs_g": 29.5, "fat_g":  0.8},
    {"name": "Sweet Potato (baked)",            "serving_size": 100, "serving_unit": "g",
     "calories":  90, "protein_g":  2.0, "carbs_g": 21.0, "fat_g":  0.1, "fiber_g": 3.3, "sugar_g": 4.2},
    {"name": "White Potato (baked)",            "serving_size": 100, "serving_unit": "g",
     "calories":  93, "protein_g":  2.5, "carbs_g": 21.0, "fat_g":  0.1, "fiber_g": 2.1},
    {"name": "Quinoa (cooked)",                 "serving_size": 100, "serving_unit": "g",
     "calories": 120, "protein_g":  4.4, "carbs_g": 21.3, "fat_g":  1.9, "fiber_g": 2.8},
    {"name": "Corn Tortilla",                   "serving_size":  26, "serving_unit": "g",
     "calories":  57, "protein_g":  1.5, "carbs_g": 11.6, "fat_g":  0.7, "fiber_g": 1.6},
    {"name": "Rice Cake (plain)",               "serving_size":   9, "serving_unit": "g",
     "calories":  35, "protein_g":  0.7, "carbs_g":  7.3, "fat_g":  0.3},
    {"name": "Granola",                         "serving_size":  50, "serving_unit": "g",
     "calories": 214, "protein_g":  5.4, "carbs_g": 32.4, "fat_g":  7.6, "fiber_g": 2.4, "sugar_g": 10.2},

    # ══════════════════════════════════════════════════════════════════════════
    # CARBOHYDRATES — FRUITS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Banana",                          "serving_size": 118, "serving_unit": "g",
     "calories": 105, "protein_g":  1.3, "carbs_g": 27.0, "fat_g":  0.4, "fiber_g": 3.1, "sugar_g": 14.4},
    {"name": "Apple",                           "serving_size": 182, "serving_unit": "g",
     "calories":  95, "protein_g":  0.5, "carbs_g": 25.0, "fat_g":  0.3, "fiber_g": 4.4, "sugar_g": 19.0},
    {"name": "Orange",                          "serving_size": 131, "serving_unit": "g",
     "calories":  62, "protein_g":  1.2, "carbs_g": 15.4, "fat_g":  0.2, "fiber_g": 3.1, "sugar_g": 12.2},
    {"name": "Blueberries",                     "serving_size": 148, "serving_unit": "g",
     "calories":  84, "protein_g":  1.1, "carbs_g": 21.4, "fat_g":  0.5, "fiber_g": 3.6, "sugar_g": 14.7},
    {"name": "Strawberries",                    "serving_size": 152, "serving_unit": "g",
     "calories":  49, "protein_g":  1.0, "carbs_g": 11.7, "fat_g":  0.5, "fiber_g": 3.0, "sugar_g":  7.4},
    {"name": "Mango",                           "serving_size": 165, "serving_unit": "g",
     "calories":  99, "protein_g":  1.4, "carbs_g": 24.7, "fat_g":  0.6, "fiber_g": 2.6, "sugar_g": 22.5},
    {"name": "Grapes",                          "serving_size": 150, "serving_unit": "g",
     "calories": 104, "protein_g":  1.1, "carbs_g": 27.3, "fat_g":  0.2, "fiber_g": 1.4, "sugar_g": 23.4},
    {"name": "Pineapple",                       "serving_size": 165, "serving_unit": "g",
     "calories":  82, "protein_g":  0.9, "carbs_g": 22.0, "fat_g":  0.2, "fiber_g": 2.3, "sugar_g": 16.3},
    {"name": "Dates (medjool)",                 "serving_size":  24, "serving_unit": "g",
     "calories":  66, "protein_g":  0.4, "carbs_g": 18.0, "fat_g":  0.0, "fiber_g": 1.6, "sugar_g": 16.0},

    # ══════════════════════════════════════════════════════════════════════════
    # CARBOHYDRATES — VEGETABLES
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Broccoli (cooked)",               "serving_size": 100, "serving_unit": "g",
     "calories":  35, "protein_g":  2.4, "carbs_g":  7.2, "fat_g":  0.4, "fiber_g": 3.3},
    {"name": "Spinach (raw)",                   "serving_size":  30, "serving_unit": "g",
     "calories":   7, "protein_g":  0.9, "carbs_g":  1.1, "fat_g":  0.1, "fiber_g": 0.7},
    {"name": "Kale (raw)",                      "serving_size":  67, "serving_unit": "g",
     "calories":  33, "protein_g":  2.2, "carbs_g":  6.7, "fat_g":  0.5, "fiber_g": 1.3},
    {"name": "Romaine Lettuce",                 "serving_size":  85, "serving_unit": "g",
     "calories":  15, "protein_g":  1.2, "carbs_g":  2.8, "fat_g":  0.2, "fiber_g": 1.9},
    {"name": "Bell Pepper (red)",               "serving_size": 119, "serving_unit": "g",
     "calories":  37, "protein_g":  1.2, "carbs_g":  7.2, "fat_g":  0.4, "fiber_g": 2.5, "sugar_g": 5.0},
    {"name": "Cucumber",                        "serving_size": 119, "serving_unit": "g",
     "calories":  16, "protein_g":  0.7, "carbs_g":  3.8, "fat_g":  0.1, "fiber_g": 0.5},
    {"name": "Cherry Tomatoes",                 "serving_size": 149, "serving_unit": "g",
     "calories":  27, "protein_g":  1.3, "carbs_g":  5.8, "fat_g":  0.3, "fiber_g": 1.8, "sugar_g": 3.9},
    {"name": "Asparagus (cooked)",              "serving_size":  90, "serving_unit": "g",
     "calories":  20, "protein_g":  2.2, "carbs_g":  3.7, "fat_g":  0.2, "fiber_g": 1.8},
    {"name": "Zucchini (cooked)",               "serving_size": 100, "serving_unit": "g",
     "calories":  17, "protein_g":  1.1, "carbs_g":  3.5, "fat_g":  0.3, "fiber_g": 1.1},
    {"name": "Carrot (raw)",                    "serving_size":  61, "serving_unit": "g",
     "calories":  25, "protein_g":  0.6, "carbs_g":  5.8, "fat_g":  0.1, "fiber_g": 1.7, "sugar_g": 2.9},
    {"name": "Green Beans (cooked)",            "serving_size": 100, "serving_unit": "g",
     "calories":  35, "protein_g":  1.9, "carbs_g":  7.9, "fat_g":  0.3, "fiber_g": 3.4},
    {"name": "Cauliflower (cooked)",            "serving_size": 100, "serving_unit": "g",
     "calories":  23, "protein_g":  1.8, "carbs_g":  4.1, "fat_g":  0.5, "fiber_g": 2.3},
    {"name": "Mushrooms (raw)",                 "serving_size":  70, "serving_unit": "g",
     "calories":  15, "protein_g":  2.2, "carbs_g":  2.3, "fat_g":  0.2, "fiber_g": 0.7},

    # ══════════════════════════════════════════════════════════════════════════
    # FATS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Avocado",                         "serving_size": 150, "serving_unit": "g",
     "calories": 240, "protein_g":  3.0, "carbs_g": 13.0, "fat_g": 22.0, "fiber_g": 10.0},
    {"name": "Almonds",                         "serving_size":  28, "serving_unit": "g",
     "calories": 164, "protein_g":  6.0, "carbs_g":  6.0, "fat_g": 14.0, "fiber_g":  3.5},
    {"name": "Walnuts",                         "serving_size":  28, "serving_unit": "g",
     "calories": 185, "protein_g":  4.3, "carbs_g":  3.9, "fat_g": 18.5, "fiber_g":  1.9},
    {"name": "Cashews",                         "serving_size":  28, "serving_unit": "g",
     "calories": 157, "protein_g":  5.2, "carbs_g":  8.6, "fat_g": 12.4, "fiber_g":  0.9},
    {"name": "Mixed Nuts",                      "serving_size":  28, "serving_unit": "g",
     "calories": 172, "protein_g":  5.0, "carbs_g":  6.0, "fat_g": 15.0, "fiber_g":  2.0},
    {"name": "Peanut Butter (natural)",         "serving_size":  32, "serving_unit": "g",
     "calories": 188, "protein_g":  8.0, "carbs_g":  7.0, "fat_g": 16.0, "fiber_g":  2.0},
    {"name": "Almond Butter",                   "serving_size":  32, "serving_unit": "g",
     "calories": 196, "protein_g":  7.0, "carbs_g":  7.0, "fat_g": 18.0, "fiber_g":  3.5},
    {"name": "Olive Oil",                       "serving_size":  14, "serving_unit": "ml",
     "calories": 119, "protein_g":  0.0, "carbs_g":  0.0, "fat_g": 13.5},
    {"name": "Coconut Oil",                     "serving_size":  14, "serving_unit": "ml",
     "calories": 121, "protein_g":  0.0, "carbs_g":  0.0, "fat_g": 14.0},
    {"name": "Flaxseed (ground)",               "serving_size":  15, "serving_unit": "g",
     "calories":  74, "protein_g":  2.6, "carbs_g":  4.0, "fat_g":  5.9, "fiber_g": 3.8},
    {"name": "Chia Seeds",                      "serving_size":  28, "serving_unit": "g",
     "calories": 138, "protein_g":  4.7, "carbs_g": 12.0, "fat_g":  8.7, "fiber_g": 9.8},

    # ══════════════════════════════════════════════════════════════════════════
    # CONDIMENTS & EXTRAS
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Honey",                           "serving_size":  21, "serving_unit": "g",
     "calories":  64, "protein_g":  0.1, "carbs_g": 17.3, "fat_g":  0.0, "sugar_g": 17.2},
    {"name": "Hummus",                          "serving_size":  30, "serving_unit": "g",
     "calories":  74, "protein_g":  2.5, "carbs_g":  6.3, "fat_g":  4.5, "fiber_g": 1.6},
    {"name": "Salsa",                           "serving_size":  30, "serving_unit": "g",
     "calories":   8, "protein_g":  0.4, "carbs_g":  1.8, "fat_g":  0.0, "fiber_g": 0.4},
    {"name": "Soy Sauce (light)",               "serving_size":  15, "serving_unit": "ml",
     "calories":   9, "protein_g":  1.0, "carbs_g":  0.8, "fat_g":  0.0},
    {"name": "Hot Sauce",                       "serving_size":   5, "serving_unit": "ml",
     "calories":   1, "protein_g":  0.1, "carbs_g":  0.1, "fat_g":  0.0},

    # ══════════════════════════════════════════════════════════════════════════
    # SNACKS & CONVENIENCE
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Protein Bar (generic)",           "serving_size":  60, "serving_unit": "g",
     "calories": 210, "protein_g": 20.0, "carbs_g": 25.0, "fat_g":  7.0, "fiber_g": 3.0, "sugar_g": 5.0},
    {"name": "Quest Bar",                       "serving_size":  60, "serving_unit": "g",
     "calories": 200, "protein_g": 21.0, "carbs_g": 22.0, "fat_g":  8.0, "fiber_g": 14.0, "sugar_g": 1.0},
    {"name": "Dark Chocolate (70%+)",           "serving_size":  28, "serving_unit": "g",
     "calories": 153, "protein_g":  2.2, "carbs_g": 12.9, "fat_g": 10.8, "fiber_g": 3.1, "sugar_g": 7.0},
    {"name": "Popcorn (plain, air-popped)",     "serving_size":  28, "serving_unit": "g",
     "calories": 110, "protein_g":  3.6, "carbs_g": 22.1, "fat_g":  1.3, "fiber_g": 4.2},
    {"name": "Greek Yogurt (flavoured, low-fat)","serving_size": 150,"serving_unit": "g",
     "calories": 130, "protein_g": 10.0, "carbs_g": 19.0, "fat_g":  1.5, "sugar_g": 17.0},

    # ══════════════════════════════════════════════════════════════════════════
    # BEVERAGES
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Orange Juice (fresh)",            "serving_size": 240, "serving_unit": "ml",
     "calories": 112, "protein_g":  1.7, "carbs_g": 26.0, "fat_g":  0.5, "sugar_g": 21.0},
    {"name": "Chocolate Milk (low-fat)",        "serving_size": 240, "serving_unit": "ml",
     "calories": 158, "protein_g":  8.1, "carbs_g": 26.0, "fat_g":  2.5, "sugar_g": 24.0},
    {"name": "Coconut Water",                   "serving_size": 240, "serving_unit": "ml",
     "calories":  46, "protein_g":  1.7, "carbs_g":  8.9, "fat_g":  0.5, "sugar_g": 6.3},
    {"name": "Black Coffee",                    "serving_size": 240, "serving_unit": "ml",
     "calories":   2, "protein_g":  0.3, "carbs_g":  0.0, "fat_g":  0.0},

    # ══════════════════════════════════════════════════════════════════════════
    # SPORTS / WORKOUT NUTRITION
    # ══════════════════════════════════════════════════════════════════════════
    {"name": "Whey Protein Powder",             "serving_size":  30, "serving_unit": "g",
     "calories": 120, "protein_g": 24.0, "carbs_g":  3.0, "fat_g":  1.5},
    {"name": "Casein Protein Powder",           "serving_size":  33, "serving_unit": "g",
     "calories": 120, "protein_g": 24.0, "carbs_g":  4.0, "fat_g":  1.0},
    {"name": "Pea Protein Powder",              "serving_size":  30, "serving_unit": "g",
     "calories": 110, "protein_g": 22.0, "carbs_g":  2.0, "fat_g":  1.0},
    {"name": "Dextrose (glucose powder)",       "serving_size":  50, "serving_unit": "g",
     "calories": 194, "protein_g":  0.0, "carbs_g": 50.0, "fat_g":  0.0, "sugar_g": 50.0},
    {"name": "Sports Drink (isotonic)",         "serving_size": 500, "serving_unit": "ml",
     "calories": 150, "protein_g":  0.0, "carbs_g": 37.5, "fat_g":  0.0, "sugar_g": 34.0},

    # ══════════════════════════════════════════════════════════════════════════
    # NEPALI HOUSEHOLD FOODS
    # Sources: USDA FoodData, Nepal Academy of Science & Technology nutritional
    # tables, and standard South-Asian nutritional references.
    # ══════════════════════════════════════════════════════════════════════════

    # ── Grains & Staples ──────────────────────────────────────────────────────
    {"name": "Chiura (beaten rice, dry)",
     "serving_size": 60, "serving_unit": "g",
     "calories": 216, "protein_g": 3.6, "carbs_g": 48.0, "fat_g": 0.6, "fiber_g": 0.6,
     # Flattened/parboiled rice flakes — common breakfast and snack base
    },
    {"name": "Dhido (buckwheat porridge, cooked)",
     "serving_size": 200, "serving_unit": "g",
     "calories": 250, "protein_g": 6.0, "carbs_g": 54.0, "fat_g": 1.6, "fiber_g": 4.0,
     # Traditional Nepali staple made from buckwheat or millet flour and water
    },
    {"name": "Roti / Chapati (whole wheat)",
     "serving_size": 30, "serving_unit": "g",
     "calories": 80,  "protein_g": 2.8, "carbs_g": 14.2, "fat_g": 1.8, "fiber_g": 2.0,
     # One medium roti; made from atta (whole-wheat flour) on a tawa
    },
    {"name": "Sel Roti (fried rice bread)",
     "serving_size": 80, "serving_unit": "g",
     "calories": 280, "protein_g": 4.0, "carbs_g": 45.0, "fat_g": 10.0, "fiber_g": 0.8,
     # Traditional ring-shaped deep-fried rice bread; popular during festivals and breakfast
    },
    {"name": "Makai ko Dhido (corn porridge, cooked)",
     "serving_size": 200, "serving_unit": "g",
     "calories": 218, "protein_g": 5.0, "carbs_g": 48.0, "fat_g": 1.0, "fiber_g": 3.0,
     # Coarse cornmeal porridge; rural breakfast and staple
    },
    {"name": "Puffed Rice (Bhuja/Murai)",
     "serving_size": 30, "serving_unit": "g",
     "calories": 114, "protein_g": 1.8, "carbs_g": 25.8, "fat_g": 0.2, "fiber_g": 0.3,
     # Light puffed rice used in chatpate, eaten as a snack
    },
    {"name": "Wai Wai Instant Noodles (raw)",
     "serving_size": 75, "serving_unit": "g",
     "calories": 351, "protein_g": 8.0, "carbs_g": 48.0, "fat_g": 14.0, "fiber_g": 1.5,
     # Nepal's iconic instant noodles; eaten raw as a snack or cooked as a meal
    },

    # ── Dal (lentil soups) ────────────────────────────────────────────────────
    {"name": "Masoor Dal (red lentil soup, cooked)",
     "serving_size": 150, "serving_unit": "ml",
     "calories": 83,  "protein_g": 6.0, "carbs_g": 12.0, "fat_g": 1.5, "fiber_g": 3.0,
     # Thin everyday dal; served with rice as part of dal-bhat
    },
    {"name": "Moong Dal (green mung soup, cooked)",
     "serving_size": 150, "serving_unit": "ml",
     "calories": 98,  "protein_g": 7.5, "carbs_g": 15.0, "fat_g": 1.0, "fiber_g": 3.5,
    },
    {"name": "Kalo Dal (black lentil/urad, cooked)",
     "serving_size": 150, "serving_unit": "ml",
     "calories": 120, "protein_g": 9.0, "carbs_g": 18.0, "fat_g": 1.5, "fiber_g": 4.5,
     # Richer, darker dal; often served at special occasions
    },
    {"name": "Kwati (mixed sprouted bean soup)",
     "serving_size": 200, "serving_unit": "ml",
     "calories": 170, "protein_g": 14.0, "carbs_g": 26.0, "fat_g": 2.0, "fiber_g": 8.0,
     # Nine-bean mix; traditional Janai Purnima dish, very nutritious
    },

    # ── Vegetables & Curries ──────────────────────────────────────────────────
    {"name": "Alu Tarkari (potato curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 135, "protein_g": 2.5, "carbs_g": 21.0, "fat_g": 4.5, "fiber_g": 3.0,
     # Spiced potato curry; the most common everyday vegetable side
    },
    {"name": "Saag (cooked spinach / mustard greens)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  42, "protein_g": 3.0, "carbs_g":  5.0, "fat_g": 1.5, "fiber_g": 3.5,
     # Sautéed leafy greens (palak or rayo); eaten with rice or roti
    },
    {"name": "Gundruk (fermented dried greens, cooked)",
     "serving_size": 50, "serving_unit": "g",
     "calories":  18, "protein_g": 1.5, "carbs_g":  2.5, "fat_g": 0.3, "fiber_g": 1.5,
     # Fermented and sun-dried leafy vegetables; tangy flavour, used as a side or pickle
    },
    {"name": "Cauliflower and Potato Curry (Cauli Aloo)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 120, "protein_g": 3.0, "carbs_g": 16.0, "fat_g": 5.0, "fiber_g": 3.5,
    },
    {"name": "Tomato Achar (fresh tomato pickle)",
     "serving_size": 30, "serving_unit": "g",
     "calories":  20, "protein_g": 0.5, "carbs_g":  3.5, "fat_g": 0.5, "fiber_g": 0.8,
     # Fresh tomato and chilli chutney; served with every Nepali meal
    },
    {"name": "Bitter Gourd Curry (Tite Karela)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  55, "protein_g": 2.0, "carbs_g":  8.0, "fat_g": 2.0, "fiber_g": 3.0,
    },

    # ── Meat & Protein ────────────────────────────────────────────────────────
    {"name": "Goat Curry (Khasi ko masu)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 285, "protein_g": 33.0, "carbs_g":  7.5, "fat_g": 13.5, "fiber_g": 0.5,
     # Bone-in goat meat in spiced onion-tomato gravy; served on special occasions
    },
    {"name": "Buff Curry (Buff ko masu)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 218, "protein_g": 39.0, "carbs_g":  6.0, "fat_g":  6.0, "fiber_g": 0.5,
     # Water buffalo meat curry; widely eaten across Nepal
    },
    {"name": "Sukuti (dried buffalo/yak meat)",
     "serving_size": 30, "serving_unit": "g",
     "calories":  75, "protein_g": 13.5, "carbs_g":  1.5, "fat_g":  1.5, "fiber_g": 0.0,
     # Spiced sun-dried meat; high-protein snack eaten with chiura or as tarkari
    },
    {"name": "Chicken Curry (Nepali style)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 240, "protein_g": 28.0, "carbs_g":  6.0, "fat_g": 11.0, "fiber_g": 0.5,
     # Bone-in chicken in aromatic masala gravy
    },
    {"name": "Fried Fish (Machha)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 185, "protein_g": 22.0, "carbs_g":  4.0, "fat_g":  9.0, "fiber_g": 0.0,
    },

    # ── Snacks ────────────────────────────────────────────────────────────────
    {"name": "Momo (steamed chicken dumplings)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 178, "protein_g": 10.0, "carbs_g": 22.0, "fat_g":  5.0, "fiber_g": 1.0,
     # ~4 pieces per 100g; Nepal's most popular street food
    },
    {"name": "Momo (steamed vegetable dumplings)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 145, "protein_g":  5.0, "carbs_g": 24.0, "fat_g":  3.5, "fiber_g": 2.0,
    },
    {"name": "Chatpate (spicy puffed rice snack)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 320, "protein_g":  7.0, "carbs_g": 58.0, "fat_g":  7.5, "fiber_g": 3.0,
     # Puffed rice tossed with spices, vegetables, and tangy chutney; street snack
    },
    {"name": "Bhatmas (roasted soybeans)",
     "serving_size": 30, "serving_unit": "g",
     "calories": 129, "protein_g": 10.8, "carbs_g":  9.0, "fat_g":  5.7, "fiber_g": 2.7,
     # Dry-roasted soybeans with salt and spices; protein-rich Nepali snack
    },
    {"name": "Samosa (vegetable, fried)",
     "serving_size": 65, "serving_unit": "g",
     "calories": 140, "protein_g":  3.0, "carbs_g": 17.0, "fat_g":  6.5, "fiber_g": 2.0,
    },
    {"name": "Pakoda (vegetable fritters)",
     "serving_size": 80, "serving_unit": "g",
     "calories": 200, "protein_g":  5.5, "carbs_g": 22.0, "fat_g":  9.5, "fiber_g": 2.5,
     # Gram-flour battered fried vegetables; common tea-time snack
    },
    {"name": "Lapsi (hog plum)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  66, "protein_g":  0.7, "carbs_g": 17.0, "fat_g":  0.4, "fiber_g": 2.0, "sugar_g": 13.0,
     # Sour-sweet Nepali hog plum; eaten fresh or as candy/pickle
    },
    {"name": "Roasted Corn (Makai)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 115, "protein_g":  3.5, "carbs_g": 25.0, "fat_g":  1.5, "fiber_g": 2.8,
     # Flame-roasted corn cob with salt and lemon; quintessential Nepali street snack
    },
    {"name": "Chow Mein (Nepali fried noodles)",
     "serving_size": 200, "serving_unit": "g",
     "calories": 300, "protein_g": 10.0, "carbs_g": 50.0, "fat_g":  8.0, "fiber_g": 3.0,
     # Stir-fried noodles with vegetables and egg/chicken; popular lunch and street food
    },

    # ── Desserts & Dairy ──────────────────────────────────────────────────────
    {"name": "Kheer (rice pudding)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 195, "protein_g":  6.0, "carbs_g": 33.0, "fat_g":  5.5, "fiber_g": 0.2, "sugar_g": 27.0,
     # Sweet rice cooked in milk with sugar; served at festivals and celebrations
    },
    {"name": "Dahi (Nepali yogurt, whole milk)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 106, "protein_g":  5.5, "carbs_g":  8.0, "fat_g":  6.0, "fiber_g": 0.0, "sugar_g": 8.0,
     # Thick set yogurt; eaten with chiura or rice, or as a dessert with sugar
    },
    {"name": "Juju Dhau (Bhaktapur king curd)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  98, "protein_g":  4.5, "carbs_g": 10.0, "fat_g":  5.0, "fiber_g": 0.0, "sugar_g": 9.5,
     # Creamy clay-pot-set yogurt from Bhaktapur; famous Newari delicacy
    },
    {"name": "Sikarni (strained yogurt with nuts and spices)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 165, "protein_g":  6.0, "carbs_g": 18.0, "fat_g":  8.0, "fiber_g": 0.5, "sugar_g": 16.0,
     # Thick strained yogurt with sugar, cardamom, saffron, and nuts; Newari sweet
    },

    # ── Beverages ─────────────────────────────────────────────────────────────
    {"name": "Chiya (Nepali milk tea, sweetened)",
     "serving_size": 180, "serving_unit": "ml",
     "calories":  75, "protein_g":  2.8, "carbs_g": 10.5, "fat_g":  2.5, "fiber_g": 0.0, "sugar_g": 9.0,
     # Strong tea brewed with full-fat milk and sugar; 2–4 cups daily is the norm
    },
    {"name": "Lassi (sweet yogurt drink)",
     "serving_size": 300, "serving_unit": "ml",
     "calories": 195, "protein_g":  7.5, "carbs_g": 30.0, "fat_g":  6.0, "fiber_g": 0.0, "sugar_g": 28.0,
    },
    {"name": "Tongba (millet beer, fermented)",
     "serving_size": 300, "serving_unit": "ml",
     "calories": 105, "protein_g":  1.5, "carbs_g": 18.0, "fat_g":  0.5, "fiber_g": 0.5,
     # Traditional Limbu/Rai fermented millet drink; low-alcohol, served warm
    },

    # ── More Nepali Grains & Breads ───────────────────────────────────────────
    {"name": "Kodo ko Roti (millet flatbread)",
     "serving_size": 40, "serving_unit": "g",
     "calories": 118, "protein_g":  3.5, "carbs_g": 22.0, "fat_g":  2.0, "fiber_g": 3.5,
    },
    {"name": "Makai ko Roti (corn flatbread)",
     "serving_size": 40, "serving_unit": "g",
     "calories": 110, "protein_g":  2.8, "carbs_g": 21.0, "fat_g":  1.5, "fiber_g": 2.5,
    },
    {"name": "Puri (deep-fried wheat bread)",
     "serving_size": 35, "serving_unit": "g",
     "calories": 120, "protein_g":  2.5, "carbs_g": 15.0, "fat_g":  5.5, "fiber_g": 0.8,
     # Puffed fried bread served with aloo tarkari; popular breakfast and festival food
    },
    {"name": "Aloo Paratha",
     "serving_size": 90, "serving_unit": "g",
     "calories": 230, "protein_g":  5.5, "carbs_g": 34.0, "fat_g":  8.5, "fiber_g": 3.0,
     # Whole-wheat flatbread stuffed with spiced mashed potato
    },
    {"name": "Gwaramari (Newari fried bread)",
     "serving_size": 60, "serving_unit": "g",
     "calories": 190, "protein_g":  4.0, "carbs_g": 28.0, "fat_g":  7.0, "fiber_g": 1.0,
     # Soft fried dough balls; a Newar breakfast specialty
    },
    {"name": "Tsampa (roasted barley flour)",
     "serving_size": 50, "serving_unit": "g",
     "calories": 182, "protein_g":  6.5, "carbs_g": 36.0, "fat_g":  2.0, "fiber_g": 5.0,
     # Staple of Sherpa and Tibetan communities; mixed with butter tea to form dough
    },
    {"name": "Tingmo (Tibetan steamed bread)",
     "serving_size": 80, "serving_unit": "g",
     "calories": 188, "protein_g":  6.0, "carbs_g": 38.0, "fat_g":  1.5, "fiber_g": 1.5,
     # Soft steamed wheat bread; common in Sherpa households and mountain regions
    },
    {"name": "Poha (flattened rice, cooked)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 244, "protein_g":  4.5, "carbs_g": 50.0, "fat_g":  3.5, "fiber_g": 1.5,
     # Chiura cooked with onion, mustard seeds, and spices; popular light breakfast
    },

    # ── More Dal & Legume Dishes ──────────────────────────────────────────────
    {"name": "Chana Dal (split chickpea soup, cooked)",
     "serving_size": 150, "serving_unit": "ml",
     "calories": 118, "protein_g":  8.0, "carbs_g": 18.0, "fat_g":  1.5, "fiber_g": 5.0,
    },
    {"name": "Toor Dal (pigeon pea soup, cooked)",
     "serving_size": 150, "serving_unit": "ml",
     "calories":  98, "protein_g":  7.0, "carbs_g": 16.0, "fat_g":  1.0, "fiber_g": 4.0,
    },
    {"name": "Panchamel Dal (five-lentil mix, cooked)",
     "serving_size": 150, "serving_unit": "ml",
     "calories": 108, "protein_g":  7.5, "carbs_g": 16.5, "fat_g":  1.5, "fiber_g": 4.5,
     # Blend of masoor, moong, chana, toor, and urad dals; richly nutritious
    },
    {"name": "Bodi ko Tarkari (black-eyed pea curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 148, "protein_g":  9.0, "carbs_g": 22.0, "fat_g":  3.0, "fiber_g": 6.0,
    },
    {"name": "Rajma (kidney bean curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 165, "protein_g":  9.5, "carbs_g": 24.0, "fat_g":  3.5, "fiber_g": 7.0,
    },
    {"name": "Kabuli Chana Curry (white chickpea curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 175, "protein_g": 10.0, "carbs_g": 25.0, "fat_g":  4.5, "fiber_g": 7.5,
    },

    # ── More Vegetables & Curries ─────────────────────────────────────────────
    {"name": "Tama (bamboo shoot curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories":  85, "protein_g":  3.5, "carbs_g": 10.0, "fat_g":  3.5, "fiber_g": 3.5,
     # Fermented bamboo shoot cooked with potato and black-eyed peas; distinctive flavour
    },
    {"name": "Pharsi ko Tarkari (pumpkin curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories":  90, "protein_g":  2.0, "carbs_g": 14.0, "fat_g":  3.0, "fiber_g": 2.5,
    },
    {"name": "Iskus ko Tarkari (chayote squash curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories":  72, "protein_g":  1.5, "carbs_g": 11.0, "fat_g":  2.5, "fiber_g": 2.0,
    },
    {"name": "Simi ko Tarkari (green bean curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories":  80, "protein_g":  3.0, "carbs_g": 10.5, "fat_g":  3.0, "fiber_g": 4.0,
    },
    {"name": "Kerau ko Tarkari (green pea curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 130, "protein_g":  6.5, "carbs_g": 18.0, "fat_g":  3.5, "fiber_g": 5.0,
    },
    {"name": "Bandakopi ko Tarkari (cabbage stir-fry)",
     "serving_size": 150, "serving_unit": "g",
     "calories":  78, "protein_g":  2.5, "carbs_g":  9.5, "fat_g":  3.5, "fiber_g": 3.5,
    },
    {"name": "Ghiraula ko Tarkari (ridge gourd curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories":  65, "protein_g":  1.5, "carbs_g":  9.0, "fat_g":  2.5, "fiber_g": 3.0,
    },
    {"name": "Baigan ko Tarkari (eggplant / brinjal curry)",
     "serving_size": 150, "serving_unit": "g",
     "calories":  88, "protein_g":  2.0, "carbs_g": 10.5, "fat_g":  4.0, "fiber_g": 3.5,
    },
    {"name": "Mushroom Tarkari",
     "serving_size": 150, "serving_unit": "g",
     "calories":  88, "protein_g":  4.5, "carbs_g":  8.0, "fat_g":  4.0, "fiber_g": 2.5,
    },
    {"name": "Paneer Curry",
     "serving_size": 150, "serving_unit": "g",
     "calories": 245, "protein_g": 12.0, "carbs_g":  8.0, "fat_g": 18.0, "fiber_g": 1.5,
    },
    {"name": "Sinki ko Achar (fermented radish pickle)",
     "serving_size": 30, "serving_unit": "g",
     "calories":   8, "protein_g":  0.5, "carbs_g":  1.5, "fat_g":  0.1, "fiber_g": 0.8,
     # Fermented dried radish taproot; pungent and sour side condiment
    },
    {"name": "Mula ko Achar (radish pickle)",
     "serving_size": 30, "serving_unit": "g",
     "calories":  12, "protein_g":  0.4, "carbs_g":  2.5, "fat_g":  0.2, "fiber_g": 0.7,
    },
    {"name": "Rayo ko Saag (mustard greens, cooked)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  35, "protein_g":  2.5, "carbs_g":  4.0, "fat_g":  1.0, "fiber_g": 2.5,
     # Pungent mustard greens sautéed in mustard oil; very common winter vegetable
    },

    # ── Rice Dishes ───────────────────────────────────────────────────────────
    {"name": "Pulao (fragrant vegetable rice)",
     "serving_size": 200, "serving_unit": "g",
     "calories": 280, "protein_g":  5.5, "carbs_g": 52.0, "fat_g":  6.0, "fiber_g": 2.0,
     # Rice cooked with whole spices, vegetables, and ghee
    },
    {"name": "Fried Rice (Nepali style)",
     "serving_size": 200, "serving_unit": "g",
     "calories": 310, "protein_g":  8.5, "carbs_g": 52.0, "fat_g":  8.0, "fiber_g": 2.0,
    },
    {"name": "Thukpa (Tibetan noodle soup)",
     "serving_size": 300, "serving_unit": "ml",
     "calories": 265, "protein_g": 12.0, "carbs_g": 38.0, "fat_g":  7.0, "fiber_g": 3.0,
     # Hearty noodle broth with vegetables and meat; Sherpa and Tibetan staple
    },

    # ── More Meat Dishes ──────────────────────────────────────────────────────
    {"name": "Sekuwa (grilled skewered meat)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 210, "protein_g": 26.0, "carbs_g":  3.0, "fat_g": 10.5, "fiber_g": 0.5,
     # Marinated grilled pork or chicken on skewers; popular street food in Kathmandu
    },
    {"name": "Choila (spiced grilled buffalo)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 185, "protein_g": 28.0, "carbs_g":  3.5, "fat_g":  6.5, "fiber_g": 0.5,
     # Grilled and spiced buffalo meat; quintessential Newari dish served at celebrations
    },
    {"name": "Pork Curry (Sungur ko masu)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 285, "protein_g": 25.0, "carbs_g":  5.0, "fat_g": 18.0, "fiber_g": 0.5,
    },
    {"name": "Chhwela (spiced raw/grilled buffalo)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 175, "protein_g": 26.0, "carbs_g":  2.5, "fat_g":  6.5, "fiber_g": 0.5,
     # Newari marinated buffalo dish; eaten with chiura
    },
    {"name": "Egg Curry (Anda ko tarkari)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 165, "protein_g": 10.5, "carbs_g":  5.5, "fat_g": 11.5, "fiber_g": 1.0,
    },
    {"name": "Fried Egg (Taareko Anda)",
     "serving_size": 55, "serving_unit": "g",
     "calories":  92, "protein_g":  6.3, "carbs_g":  0.5, "fat_g":  7.0, "fiber_g": 0.0,
    },

    # ── Newari Specialties ────────────────────────────────────────────────────
    {"name": "Bara (black lentil patties, fried)",
     "serving_size": 60, "serving_unit": "g",
     "calories": 145, "protein_g":  8.5, "carbs_g": 16.0, "fat_g":  5.0, "fiber_g": 2.5,
     # Crispy fried urad dal patties; Newari breakfast staple
    },
    {"name": "Chatamari (rice flour crepe)",
     "serving_size": 80, "serving_unit": "g",
     "calories": 155, "protein_g":  5.0, "carbs_g": 28.0, "fat_g":  3.0, "fiber_g": 0.5,
     # Thin rice flour crepe topped with egg or minced meat; Newari pizza
    },
    {"name": "Yomari (rice flour dumpling, sesame filling)",
     "serving_size": 55, "serving_unit": "g",
     "calories": 115, "protein_g":  2.0, "carbs_g": 22.0, "fat_g":  2.5, "fiber_g": 0.5,
     # Sweet fish-shaped dumpling filled with chaku (molasses) and sesame; Yomari Punhi festival
    },
    {"name": "Ailu (spiced mashed potato, Newari)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  95, "protein_g":  2.0, "carbs_g": 14.5, "fat_g":  3.5, "fiber_g": 2.0,
     # Mashed potato with sesame, fenugreek, and mustard oil; served with bara and chiura
    },

    # ── Street Foods & Snacks ─────────────────────────────────────────────────
    {"name": "Pani Puri / Golgappa",
     "serving_size": 100, "serving_unit": "g",
     "calories": 172, "protein_g":  3.5, "carbs_g": 30.0, "fat_g":  4.5, "fiber_g": 2.5,
     # Crispy hollow balls filled with spiced tamarind water; ubiquitous street snack
    },
    {"name": "Chana Chaat (spiced chickpea salad)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 195, "protein_g": 10.0, "carbs_g": 28.0, "fat_g":  5.0, "fiber_g": 7.0,
    },
    {"name": "Aloo Chop (spiced potato patty, fried)",
     "serving_size": 70, "serving_unit": "g",
     "calories": 155, "protein_g":  3.0, "carbs_g": 20.0, "fat_g":  7.0, "fiber_g": 2.0,
    },
    {"name": "Jhol Momo (momo in spicy soup broth)",
     "serving_size": 200, "serving_unit": "g",
     "calories": 230, "protein_g": 11.5, "carbs_g": 28.0, "fat_g":  7.5, "fiber_g": 2.0,
    },
    {"name": "C-Momo (crispy fried momo)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 265, "protein_g": 10.5, "carbs_g": 26.0, "fat_g": 13.0, "fiber_g": 1.5,
    },
    {"name": "Thukpa Fing (glass noodle soup)",
     "serving_size": 300, "serving_unit": "ml",
     "calories": 185, "protein_g":  7.0, "carbs_g": 30.0, "fat_g":  4.0, "fiber_g": 1.5,
    },
    {"name": "Anarsa (rice flour sweet)",
     "serving_size": 25, "serving_unit": "g",
     "calories":  98, "protein_g":  1.0, "carbs_g": 16.5, "fat_g":  3.5, "fiber_g": 0.3,
     # Sesame-coated fried sweet made from soaked rice; Tihar festival specialty
    },
    {"name": "Lakhamari (fried wheat pastry)",
     "serving_size": 30, "serving_unit": "g",
     "calories": 118, "protein_g":  2.0, "carbs_g": 18.5, "fat_g":  4.5, "fiber_g": 0.5,
     # Ornamental fried pastry made at festivals; given as offering and gift
    },
    {"name": "Fini Roti (layered crispy flatbread)",
     "serving_size": 50, "serving_unit": "g",
     "calories": 175, "protein_g":  4.0, "carbs_g": 28.0, "fat_g":  6.0, "fiber_g": 1.0,
     # Paper-thin layered fried bread; popular at Eid and festivals
    },

    # ── Sweets & Desserts ─────────────────────────────────────────────────────
    {"name": "Halwa (semolina/wheat, ghee-roasted)",
     "serving_size": 100, "serving_unit": "g",
     "calories": 285, "protein_g":  4.5, "carbs_g": 42.0, "fat_g": 11.0, "fiber_g": 1.0, "sugar_g": 22.0,
    },
    {"name": "Gulab Jamun (fried milk balls in syrup)",
     "serving_size": 60, "serving_unit": "g",
     "calories": 175, "protein_g":  3.0, "carbs_g": 30.0, "fat_g":  5.0, "fiber_g": 0.2, "sugar_g": 25.0,
    },
    {"name": "Rasgulla (spongy cheese balls in syrup)",
     "serving_size": 60, "serving_unit": "g",
     "calories": 108, "protein_g":  3.5, "carbs_g": 20.0, "fat_g":  2.0, "fiber_g": 0.0, "sugar_g": 18.0,
    },
    {"name": "Barfi (milk fudge)",
     "serving_size": 40, "serving_unit": "g",
     "calories": 165, "protein_g":  4.0, "carbs_g": 24.0, "fat_g":  6.5, "fiber_g": 0.2, "sugar_g": 22.0,
    },
    {"name": "Sewai (vermicelli sweet, milk-based)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 210, "protein_g":  5.5, "carbs_g": 32.0, "fat_g":  7.0, "fiber_g": 0.5, "sugar_g": 18.0,
    },

    # ── Dairy & Cheese ────────────────────────────────────────────────────────
    {"name": "Chhurpi (hard yak/cow cheese)",
     "serving_size": 20, "serving_unit": "g",
     "calories":  52, "protein_g":  8.0, "carbs_g":  1.0, "fat_g":  2.0, "fiber_g": 0.0,
     # Rock-hard fermented cheese; chewed slowly as a long-lasting snack in the mountains
    },
    {"name": "Soft Chhurpi (fresh yak cheese)",
     "serving_size": 50, "serving_unit": "g",
     "calories":  88, "protein_g": 10.5, "carbs_g":  2.0, "fat_g":  4.5, "fiber_g": 0.0,
     # Soft fresh chhurpi; milder and creamier than the hard variety
    },
    {"name": "Paneer (fresh Indian cheese)",
     "serving_size": 50, "serving_unit": "g",
     "calories": 133, "protein_g":  7.0, "carbs_g":  1.5, "fat_g": 11.0, "fiber_g": 0.0,
    },
    {"name": "Ghee (clarified butter)",
     "serving_size": 10, "serving_unit": "g",
     "calories":  90, "protein_g":  0.0, "carbs_g":  0.0, "fat_g": 10.0, "fiber_g": 0.0,
     # Used as cooking fat and finishing for dal bhat; also drizzled on dhido and roti
    },

    # ── Cooking Oils & Fats ───────────────────────────────────────────────────
    {"name": "Mustard Oil",
     "serving_size": 10, "serving_unit": "ml",
     "calories":  88, "protein_g":  0.0, "carbs_g":  0.0, "fat_g": 10.0, "fiber_g": 0.0,
     # Primary cooking oil in most Nepali households; strong pungent flavour
    },

    # ── Fruits Common in Nepal ────────────────────────────────────────────────
    {"name": "Guava (Amboo)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  68, "protein_g":  2.6, "carbs_g": 14.3, "fat_g":  1.0, "fiber_g": 5.4, "sugar_g": 8.9,
    },
    {"name": "Pomelo / Bhogate",
     "serving_size": 100, "serving_unit": "g",
     "calories":  38, "protein_g":  0.8, "carbs_g":  9.6, "fat_g":  0.0, "fiber_g": 1.0, "sugar_g": 8.5,
     # Large citrus fruit; traditional Tihar offering; eaten with salt and chilli
    },
    {"name": "Jackfruit (Kathar, ripe)",
     "serving_size": 100, "serving_unit": "g",
     "calories":  95, "protein_g":  1.7, "carbs_g": 23.5, "fat_g":  0.6, "fiber_g": 1.5, "sugar_g": 19.1,
    },
    {"name": "Green Jackfruit Curry (Kacho Kathar)",
     "serving_size": 150, "serving_unit": "g",
     "calories": 110, "protein_g":  3.5, "carbs_g": 15.0, "fat_g":  4.5, "fiber_g": 4.0,
     # Unripe jackfruit cooked as a meat substitute; popular vegetarian curry
    },
    {"name": "Lychee",
     "serving_size": 100, "serving_unit": "g",
     "calories":  66, "protein_g":  0.8, "carbs_g": 16.5, "fat_g":  0.4, "fiber_g": 1.3, "sugar_g": 15.2,
    },
    {"name": "Amala / Amla (Indian gooseberry)",
     "serving_size": 50, "serving_unit": "g",
     "calories":  22, "protein_g":  0.5, "carbs_g":  5.0, "fat_g":  0.1, "fiber_g": 1.5, "sugar_g": 3.0,
     # Extremely tart; eaten raw with salt, or as murabba/pickle; high in Vitamin C
    },

    # ── More Beverages ────────────────────────────────────────────────────────
    {"name": "Black Tea (Kalo Chiya, no milk)",
     "serving_size": 240, "serving_unit": "ml",
     "calories":   4, "protein_g":  0.1, "carbs_g":  0.7, "fat_g":  0.0, "fiber_g": 0.0,
    },
    {"name": "Butter Tea (Po Cha / Tibetan)",
     "serving_size": 240, "serving_unit": "ml",
     "calories":  78, "protein_g":  1.5, "carbs_g":  1.5, "fat_g":  7.5, "fiber_g": 0.0,
     # Tea churned with yak butter and salt; staple of mountain communities
    },
    {"name": "Sugarcane Juice (Unkhu ko Ras)",
     "serving_size": 240, "serving_unit": "ml",
     "calories": 112, "protein_g":  0.3, "carbs_g": 27.5, "fat_g":  0.0, "fiber_g": 0.0, "sugar_g": 26.0,
     # Fresh-pressed cane juice; popular street beverage especially in Terai
    },
    {"name": "Fresh Lime Soda (Nimbu Soda)",
     "serving_size": 300, "serving_unit": "ml",
     "calories":  42, "protein_g":  0.2, "carbs_g": 10.5, "fat_g":  0.0, "fiber_g": 0.0, "sugar_g": 9.0,
    },
    {"name": "Aila (Newari distilled rice spirit)",
     "serving_size": 30, "serving_unit": "ml",
     "calories":  75, "protein_g":  0.0, "carbs_g":  0.0, "fat_g":  0.0, "fiber_g": 0.0,
     # Traditional Newari home-distilled spirit; served at all Newari celebrations
    },
]


class Command(BaseCommand):
    help = "Seed the food library (safe to re-run — uses update_or_create on name)."

    def handle(self, *args, **options):
        # Deduplicate by name in case the list above has repeats
        seen = set()
        unique_foods = []
        for f in FOODS:
            if f["name"] not in seen:
                seen.add(f["name"])
                unique_foods.append(f)

        created = updated = 0
        for payload in unique_foods:
            payload.setdefault("fiber_g", 0)
            payload.setdefault("sugar_g", 0)
            _, was_created = Food.objects.update_or_create(
                name=payload["name"], brand="",
                defaults={**payload, "is_public": True},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded foods: {created} created, {updated} updated "
            f"({len(unique_foods)} total)."
        ))
