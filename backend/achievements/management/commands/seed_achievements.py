from django.core.management.base import BaseCommand

from achievements.models import Achievement

K = Achievement.Kind

ACHIEVEMENTS = [
    # ── Workout count ─────────────────────────────────────────────────────────
    {"code": "first_workout",  "name": "First Step",               "description": "Complete your very first workout. Every legend starts somewhere.",                    "icon": "rocket",        "kind": K.WORKOUT_COUNT, "threshold": 1},
    {"code": "workouts_10",    "name": "Getting Started",           "description": "10 workouts done. The habit is forming.",                                           "icon": "flame",         "kind": K.WORKOUT_COUNT, "threshold": 10},
    {"code": "workouts_25",    "name": "Quarter Century",           "description": "25 workouts in the books. You mean business.",                                      "icon": "trending-up",   "kind": K.WORKOUT_COUNT, "threshold": 25},
    {"code": "workouts_50",    "name": "Dedicated",                 "description": "50 workouts. This is no longer a phase — it's a lifestyle.",                        "icon": "medal",         "kind": K.WORKOUT_COUNT, "threshold": 50},
    {"code": "workouts_100",   "name": "Centurion",                 "description": "100 workouts completed. You're in rare company.",                                   "icon": "trophy",        "kind": K.WORKOUT_COUNT, "threshold": 100},
    {"code": "workouts_200",   "name": "Obsessed (In a Good Way)",  "description": "200 workouts. Most people quit at 10.",                                             "icon": "star",          "kind": K.WORKOUT_COUNT, "threshold": 200},
    {"code": "workouts_365",   "name": "Year-Round Athlete",        "description": "365 workouts — a full year's worth of sessions. Elite.",                            "icon": "calendar-check","kind": K.WORKOUT_COUNT, "threshold": 365},
    {"code": "workouts_500",   "name": "Legend Status",             "description": "500 workouts. The gym practically has your name on it.",                            "icon": "crown",         "kind": K.WORKOUT_COUNT, "threshold": 500},
    # ── Streak ────────────────────────────────────────────────────────────────
    {"code": "streak_3",       "name": "On a Roll",                 "description": "3 days in a row. Momentum is everything.",                                          "icon": "zap",           "kind": K.STREAK_DAYS, "threshold": 3},
    {"code": "streak_7",       "name": "Week Warrior",              "description": "7 consecutive days. A full week without breaking.",                                 "icon": "calendar",      "kind": K.STREAK_DAYS, "threshold": 7},
    {"code": "streak_14",      "name": "Fortnight Fire",            "description": "14 days straight. Two weeks of zero excuses.",                                      "icon": "flame",         "kind": K.STREAK_DAYS, "threshold": 14},
    {"code": "streak_30",      "name": "Iron Habit",                "description": "30 days in a row. Science says 21 days — you proved them wrong.",                  "icon": "shield",        "kind": K.STREAK_DAYS, "threshold": 30},
    {"code": "streak_60",      "name": "Two-Month Titan",           "description": "60 consecutive training days. You don't take days off.",                           "icon": "shield-check",  "kind": K.STREAK_DAYS, "threshold": 60},
    {"code": "streak_100",     "name": "Centurion Streak",          "description": "100 days without stopping. Triple digits. Unreal.",                                 "icon": "award",         "kind": K.STREAK_DAYS, "threshold": 100},
    {"code": "streak_365",     "name": "Unbreakable",               "description": "365 consecutive days. A full year. You are the standard.",                         "icon": "infinity",      "kind": K.STREAK_DAYS, "threshold": 365},
    # ── Volume (kg lifted) ────────────────────────────────────────────────────
    {"code": "volume_1k",      "name": "Moving Mountains",          "description": "Lift your first 1,000 kg of total volume.",                                         "icon": "dumbbell",      "kind": K.VOLUME_TOTAL, "threshold": 1_000},
    {"code": "volume_5k",      "name": "Steel Bones",               "description": "5,000 kg moved. Your body is built differently now.",                              "icon": "dumbbell",      "kind": K.VOLUME_TOTAL, "threshold": 5_000},
    {"code": "volume_10k",     "name": "Heavy Hitter",              "description": "10,000 kg of total lifting volume.",                                                "icon": "dumbbell",      "kind": K.VOLUME_TOTAL, "threshold": 10_000},
    {"code": "volume_25k",     "name": "Iron Giant",                "description": "25,000 kg lifted. A small car's worth of iron, raised by you.",                    "icon": "dumbbell",      "kind": K.VOLUME_TOTAL, "threshold": 25_000},
    {"code": "volume_50k",     "name": "Power Station",             "description": "50,000 kg total volume. You're basically a machine.",                              "icon": "zap",           "kind": K.VOLUME_TOTAL, "threshold": 50_000},
    {"code": "volume_100k",    "name": "Power Lifter",              "description": "100,000 kg lifted. Six figures of iron. Legendary.",                               "icon": "trophy",        "kind": K.VOLUME_TOTAL, "threshold": 100_000},
    {"code": "volume_250k",    "name": "Quartermaster",             "description": "A quarter million kg of total lifting volume. Words fail.",                         "icon": "crown",         "kind": K.VOLUME_TOTAL, "threshold": 250_000},
    {"code": "volume_1m",      "name": "Ton Club",                  "description": "One million kg. You have officially transcended fitness.",                          "icon": "star",          "kind": K.VOLUME_TOTAL, "threshold": 1_000_000},
    # ── Workout minutes ───────────────────────────────────────────────────────
    {"code": "minutes_100",    "name": "First Hours",               "description": "100 minutes of training logged. The clock is on your side.",                        "icon": "clock",         "kind": K.WORKOUT_MINUTES, "threshold": 100},
    {"code": "minutes_300",    "name": "5 Hours In",                "description": "300 minutes — 5 solid hours of work.",                                             "icon": "clock",         "kind": K.WORKOUT_MINUTES, "threshold": 300},
    {"code": "minutes_600",    "name": "Ten Hours Strong",           "description": "600 minutes. 10 full hours under the iron.",                                       "icon": "timer",         "kind": K.WORKOUT_MINUTES, "threshold": 600},
    {"code": "minutes_1500",   "name": "Marathon Mind",             "description": "1,500 minutes — 25 hours of pure commitment.",                                     "icon": "timer",         "kind": K.WORKOUT_MINUTES, "threshold": 1_500},
    {"code": "minutes_3000",   "name": "Fifty Hour Club",           "description": "3,000 minutes — 50 hours of training.",                                            "icon": "hourglass",     "kind": K.WORKOUT_MINUTES, "threshold": 3_000},
    {"code": "minutes_6000",   "name": "Century Hours",             "description": "6,000 minutes — a hundred hours of sweat and discipline.",                          "icon": "hourglass",     "kind": K.WORKOUT_MINUTES, "threshold": 6_000},
    {"code": "minutes_10000",  "name": "Time Mastery",              "description": "10,000 minutes of training. Time well spent — every single minute.",               "icon": "crown",         "kind": K.WORKOUT_MINUTES, "threshold": 10_000},
    # ── Calories burned ───────────────────────────────────────────────────────
    {"code": "calories_1k",    "name": "Kindling",                  "description": "Burn 1,000 calories across your workouts. The fire has started.",                   "icon": "flame",         "kind": K.CALORIE_BURN, "threshold": 1_000},
    {"code": "calories_5k",    "name": "Burning Up",                "description": "5,000 calories torched. Your metabolism thanks you.",                              "icon": "flame",         "kind": K.CALORIE_BURN, "threshold": 5_000},
    {"code": "calories_25k",   "name": "Inferno",                   "description": "25,000 calories burned. You're running on pure willpower.",                        "icon": "flame",         "kind": K.CALORIE_BURN, "threshold": 25_000},
    {"code": "calories_100k",  "name": "Human Furnace",             "description": "100,000 calories obliterated. You're a force of nature.",                          "icon": "zap",           "kind": K.CALORIE_BURN, "threshold": 100_000},
    # ── Distance (km) — from watch-synced workouts ────────────────────────────
    {"code": "distance_5k",    "name": "First 5K",                  "description": "Cover your first 5 km in recorded workouts. Every journey begins here.",            "icon": "map-pin",       "kind": K.DISTANCE_KM, "threshold": 5},
    {"code": "distance_21k",   "name": "Half-Marathon Soul",        "description": "21 km covered — half-marathon distance in the books.",                             "icon": "map",           "kind": K.DISTANCE_KM, "threshold": 21},
    {"code": "distance_42k",   "name": "Marathon Legs",             "description": "42 km covered. A full marathon worth of ground.",                                  "icon": "map",           "kind": K.DISTANCE_KM, "threshold": 42},
    {"code": "distance_100k",  "name": "Century Mover",             "description": "100 km total. Your feet have done serious work.",                                  "icon": "navigation",    "kind": K.DISTANCE_KM, "threshold": 100},
    {"code": "distance_500k",  "name": "Tour de Force",             "description": "500 km covered. That's basically a road trip.",                                    "icon": "trophy",        "kind": K.DISTANCE_KM, "threshold": 500},
    {"code": "distance_1000k", "name": "Thousand K Club",           "description": "1,000 km. The distance from one end of a country to the other.",                  "icon": "crown",         "kind": K.DISTANCE_KM, "threshold": 1_000},
    # ── Early bird ────────────────────────────────────────────────────────────
    {"code": "early_bird_5",   "name": "Early Bird",                "description": "Complete 5 workouts before 7 am. The early morning belongs to you.",                "icon": "sunrise",       "kind": K.EARLY_BIRD, "threshold": 5},
    {"code": "early_bird_20",  "name": "Dawn Patrol",               "description": "20 pre-dawn sessions. While the world sleeps, you train.",                         "icon": "sunrise",       "kind": K.EARLY_BIRD, "threshold": 20},
    {"code": "early_bird_50",  "name": "Sunrise Warrior",           "description": "50 workouts before 7 am. The sun rises just to watch you.",                        "icon": "sun",           "kind": K.EARLY_BIRD, "threshold": 50},
    # ── Night owl ─────────────────────────────────────────────────────────────
    {"code": "night_owl_5",    "name": "Night Owl",                 "description": "Complete 5 workouts at 9 pm or later. Late nights, big gains.",                     "icon": "moon",          "kind": K.NIGHT_OWL, "threshold": 5},
    {"code": "night_owl_20",   "name": "Midnight Grinder",          "description": "20 late-night sessions. When others wind down, you warm up.",                      "icon": "moon",          "kind": K.NIGHT_OWL, "threshold": 20},
    {"code": "night_owl_50",   "name": "Never Sleeps",              "description": "50 workouts after 9 pm. You are the night.",                                       "icon": "moon",          "kind": K.NIGHT_OWL, "threshold": 50},
    # ── Goals completed ───────────────────────────────────────────────────────
    {"code": "goals_1",        "name": "First Win",                 "description": "Achieve your very first goal. Proof that you mean what you set.",                   "icon": "target",        "kind": K.GOALS_COMPLETED, "threshold": 1},
    {"code": "goals_5",        "name": "Goal Machine",              "description": "5 goals achieved. You don't just set goals — you crush them.",                     "icon": "target",        "kind": K.GOALS_COMPLETED, "threshold": 5},
    {"code": "goals_10",       "name": "Dream Chaser",              "description": "10 goals completed. You're the type of person others aspire to be.",               "icon": "star",          "kind": K.GOALS_COMPLETED, "threshold": 10},
    {"code": "goals_25",       "name": "Unstoppable",               "description": "25 goals achieved. Setting goals is just a formality at this point.",               "icon": "crown",         "kind": K.GOALS_COMPLETED, "threshold": 25},
]


class Command(BaseCommand):
    help = "Seed the achievement catalog (safe to re-run — uses update_or_create)."

    def handle(self, *args, **options):
        created = updated = 0
        for payload in ACHIEVEMENTS:
            _, was_created = Achievement.objects.update_or_create(
                code=payload["code"], defaults=payload
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Achievements seeded: {created} created, {updated} updated "
            f"({len(ACHIEVEMENTS)} total)."
        ))
