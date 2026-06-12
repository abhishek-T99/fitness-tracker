from django.core.management.base import BaseCommand

from achievements.models import Achievement

ACHIEVEMENTS = [
    # Workout count milestones
    {"code": "first_workout", "name": "First Step", "description": "Complete your first workout.",
     "icon": "rocket", "kind": Achievement.Kind.WORKOUT_COUNT, "threshold": 1},
    {"code": "ten_workouts", "name": "Getting Going", "description": "Complete 10 workouts.",
     "icon": "flame", "kind": Achievement.Kind.WORKOUT_COUNT, "threshold": 10},
    {"code": "fifty_workouts", "name": "Dedicated", "description": "Complete 50 workouts.",
     "icon": "medal", "kind": Achievement.Kind.WORKOUT_COUNT, "threshold": 50},
    {"code": "hundred_workouts", "name": "Centurion", "description": "Complete 100 workouts.",
     "icon": "trophy", "kind": Achievement.Kind.WORKOUT_COUNT, "threshold": 100},
    # Streak milestones
    {"code": "streak_3", "name": "On a Roll", "description": "Train 3 days in a row.",
     "icon": "zap", "kind": Achievement.Kind.STREAK_DAYS, "threshold": 3},
    {"code": "streak_7", "name": "Week Warrior", "description": "Train 7 days in a row.",
     "icon": "calendar", "kind": Achievement.Kind.STREAK_DAYS, "threshold": 7},
    {"code": "streak_30", "name": "Iron Habit", "description": "Train 30 days in a row.",
     "icon": "shield", "kind": Achievement.Kind.STREAK_DAYS, "threshold": 30},
    # Volume milestones (kg lifted total)
    {"code": "volume_10k", "name": "Heavy Hitter", "description": "Lift 10,000 kg total volume.",
     "icon": "dumbbell", "kind": Achievement.Kind.VOLUME_TOTAL, "threshold": 10000},
    {"code": "volume_100k", "name": "Power Lifter", "description": "Lift 100,000 kg total volume.",
     "icon": "dumbbell", "kind": Achievement.Kind.VOLUME_TOTAL, "threshold": 100000},
    # Minute milestones
    {"code": "minutes_300", "name": "5 Hours In", "description": "Log 300 minutes of training.",
     "icon": "clock", "kind": Achievement.Kind.WORKOUT_MINUTES, "threshold": 300},
    {"code": "minutes_1500", "name": "Marathon Mind", "description": "Log 1,500 minutes of training.",
     "icon": "clock", "kind": Achievement.Kind.WORKOUT_MINUTES, "threshold": 1500},
]


class Command(BaseCommand):
    help = "Seed the achievement catalog."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for payload in ACHIEVEMENTS:
            _, was_created = Achievement.objects.update_or_create(
                code=payload["code"], defaults=payload
            )
            created += int(was_created)
            updated += int(not was_created)
        self.stdout.write(self.style.SUCCESS(
            f"Seeded achievements: {created} created, {updated} updated."
        ))
