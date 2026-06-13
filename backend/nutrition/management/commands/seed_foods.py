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
