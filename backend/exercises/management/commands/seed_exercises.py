from django.core.management.base import BaseCommand
from django.utils.text import slugify

from exercises.models import Category, Equipment, Exercise, MuscleGroup


EXERCISES = [
    # Chest
    {"name": "Bench Press", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CHEST,
     "secondary_muscles": ["triceps", "shoulders"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Lie on a flat bench, lower the bar to mid-chest, press up to full extension."},
    {"name": "Incline Dumbbell Press", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CHEST,
     "secondary_muscles": ["shoulders", "triceps"], "equipment": Equipment.DUMBBELL,
     "is_compound": True, "instructions": "Set bench to 30-45 degrees. Press dumbbells up and slightly inward."},
    {"name": "Push-up", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CHEST,
     "secondary_muscles": ["triceps", "core"], "equipment": Equipment.BODYWEIGHT,
     "is_compound": True, "instructions": "Keep body straight, lower chest to the floor, push back up."},
    {"name": "Cable Fly", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CHEST,
     "secondary_muscles": ["shoulders"], "equipment": Equipment.CABLE,
     "instructions": "Bring cable handles together in front of the chest in a hugging motion."},
    # Back
    {"name": "Deadlift", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.BACK,
     "secondary_muscles": ["glutes", "hamstrings", "core"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Hinge at the hips, grip the bar, drive through the heels to lockout."},
    {"name": "Pull-up", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.BACK,
     "secondary_muscles": ["biceps"], "equipment": Equipment.BODYWEIGHT,
     "is_compound": True, "instructions": "Hang from bar with overhand grip, pull chin above the bar."},
    {"name": "Bent-Over Row", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.BACK,
     "secondary_muscles": ["biceps", "core"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Hinge forward 45 degrees, row the bar to lower chest."},
    {"name": "Lat Pulldown", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.BACK,
     "secondary_muscles": ["biceps"], "equipment": Equipment.CABLE,
     "instructions": "Pull bar down to upper chest, control on the way back up."},
    {"name": "Seated Cable Row", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.BACK,
     "secondary_muscles": ["biceps"], "equipment": Equipment.CABLE,
     "instructions": "Sit upright, pull handle to lower ribs, squeeze shoulder blades."},
    # Shoulders
    {"name": "Overhead Press", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.SHOULDERS,
     "secondary_muscles": ["triceps", "core"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Stand with bar at shoulders, press overhead to lockout."},
    {"name": "Lateral Raise", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.SHOULDERS,
     "equipment": Equipment.DUMBBELL,
     "instructions": "Raise dumbbells out to the side until arms parallel to the floor."},
    {"name": "Face Pull", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.SHOULDERS,
     "secondary_muscles": ["back"], "equipment": Equipment.CABLE,
     "instructions": "Pull cable rope toward face, externally rotating the shoulders."},
    # Arms
    {"name": "Barbell Curl", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.BICEPS,
     "equipment": Equipment.BARBELL,
     "instructions": "Curl the bar from hip to chest, keeping elbows pinned."},
    {"name": "Hammer Curl", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.BICEPS,
     "secondary_muscles": ["forearms"], "equipment": Equipment.DUMBBELL,
     "instructions": "Curl dumbbells with neutral grip (palms facing each other)."},
    {"name": "Tricep Pushdown", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.TRICEPS,
     "equipment": Equipment.CABLE,
     "instructions": "Press the cable attachment down until elbows are fully extended."},
    {"name": "Skull Crusher", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.TRICEPS,
     "equipment": Equipment.BARBELL,
     "instructions": "Lie on bench, lower bar to forehead, extend back to lockout."},
    # Legs
    {"name": "Back Squat", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.QUADS,
     "secondary_muscles": ["glutes", "hamstrings", "core"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Bar on upper back. Squat below parallel, drive up through heels."},
    {"name": "Front Squat", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.QUADS,
     "secondary_muscles": ["core", "glutes"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Bar on front delts, elbows high. Squat with an upright torso."},
    {"name": "Romanian Deadlift", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.HAMSTRINGS,
     "secondary_muscles": ["glutes", "back"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Hinge at hips with soft knees, lower bar along thighs to mid-shin."},
    {"name": "Walking Lunge", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.QUADS,
     "secondary_muscles": ["glutes"], "equipment": Equipment.DUMBBELL,
     "instructions": "Step forward into a lunge, drive off the front heel to step into the next lunge."},
    {"name": "Leg Press", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.QUADS,
     "secondary_muscles": ["glutes"], "equipment": Equipment.MACHINE,
     "instructions": "Press the sled until legs are nearly straight, control the descent."},
    {"name": "Hip Thrust", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.GLUTES,
     "secondary_muscles": ["hamstrings"], "equipment": Equipment.BARBELL,
     "is_compound": True, "instructions": "Shoulders on bench, bar across hips, drive hips to full extension."},
    {"name": "Calf Raise", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CALVES,
     "equipment": Equipment.MACHINE,
     "instructions": "Press through the balls of the feet to full extension, pause, lower under control."},
    # Core
    {"name": "Plank", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CORE,
     "equipment": Equipment.BODYWEIGHT,
     "instructions": "Hold a straight body line on forearms and toes. Brace the abs throughout."},
    {"name": "Hanging Leg Raise", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CORE,
     "equipment": Equipment.BODYWEIGHT,
     "instructions": "Hang from bar, raise legs to horizontal (or higher) with control."},
    {"name": "Cable Crunch", "category": Category.STRENGTH, "primary_muscle": MuscleGroup.CORE,
     "equipment": Equipment.CABLE,
     "instructions": "Kneel, hold rope behind head, crunch the torso toward the floor."},
    # Cardio
    {"name": "Running", "category": Category.CARDIO, "primary_muscle": MuscleGroup.CARDIO,
     "equipment": Equipment.CARDIO, "met_value": 9.8,
     "instructions": "Steady-state or interval running, outdoor or treadmill."},
    {"name": "Cycling", "category": Category.CARDIO, "primary_muscle": MuscleGroup.CARDIO,
     "equipment": Equipment.CARDIO, "met_value": 7.5,
     "instructions": "Stationary or outdoor cycling at moderate to vigorous pace."},
    {"name": "Rowing", "category": Category.CARDIO, "primary_muscle": MuscleGroup.CARDIO,
     "equipment": Equipment.CARDIO, "met_value": 8.5,
     "instructions": "Drive with legs, lean back, pull handle to ribs."},
    {"name": "Jump Rope", "category": Category.CARDIO, "primary_muscle": MuscleGroup.CARDIO,
     "equipment": Equipment.OTHER, "met_value": 12.3,
     "instructions": "Light bounce, rotate the rope with the wrists."},
    {"name": "Burpees", "category": Category.CARDIO, "primary_muscle": MuscleGroup.FULL_BODY,
     "equipment": Equipment.BODYWEIGHT, "met_value": 8.0,
     "instructions": "Squat, kick legs back to plank, do a push-up, return to feet, jump."},
    # Flexibility
    {"name": "Yoga Flow", "category": Category.FLEXIBILITY, "primary_muscle": MuscleGroup.FULL_BODY,
     "equipment": Equipment.BODYWEIGHT, "met_value": 3.0,
     "instructions": "Series of yoga postures linked with breath."},
    {"name": "Foam Rolling", "category": Category.FLEXIBILITY, "primary_muscle": MuscleGroup.FULL_BODY,
     "equipment": Equipment.OTHER, "met_value": 2.5,
     "instructions": "Roll major muscle groups for 60-90 seconds each."},
]


class Command(BaseCommand):
    help = "Seed the database with a starter exercise library."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for payload in EXERCISES:
            payload["slug"] = slugify(payload["name"])
            obj, was_created = Exercise.objects.update_or_create(
                slug=payload["slug"], defaults=payload
            )
            created += int(was_created)
            updated += int(not was_created)
        self.stdout.write(self.style.SUCCESS(
            f"Seeded exercises: {created} created, {updated} updated."
        ))
