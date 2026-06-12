from django.db import models


class MuscleGroup(models.TextChoices):
    CHEST = "chest", "Chest"
    BACK = "back", "Back"
    SHOULDERS = "shoulders", "Shoulders"
    BICEPS = "biceps", "Biceps"
    TRICEPS = "triceps", "Triceps"
    FOREARMS = "forearms", "Forearms"
    CORE = "core", "Core"
    QUADS = "quads", "Quadriceps"
    HAMSTRINGS = "hamstrings", "Hamstrings"
    GLUTES = "glutes", "Glutes"
    CALVES = "calves", "Calves"
    FULL_BODY = "full_body", "Full body"
    CARDIO = "cardio", "Cardio"


class Equipment(models.TextChoices):
    BODYWEIGHT = "bodyweight", "Bodyweight"
    BARBELL = "barbell", "Barbell"
    DUMBBELL = "dumbbell", "Dumbbell"
    KETTLEBELL = "kettlebell", "Kettlebell"
    MACHINE = "machine", "Machine"
    CABLE = "cable", "Cable"
    BAND = "band", "Resistance band"
    CARDIO = "cardio", "Cardio equipment"
    OTHER = "other", "Other"


class Category(models.TextChoices):
    STRENGTH = "strength", "Strength"
    CARDIO = "cardio", "Cardio"
    FLEXIBILITY = "flexibility", "Flexibility"
    BALANCE = "balance", "Balance"


class Exercise(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    primary_muscle = models.CharField(max_length=20, choices=MuscleGroup.choices)
    secondary_muscles = models.JSONField(default=list, blank=True)
    equipment = models.CharField(max_length=20, choices=Equipment.choices, default=Equipment.BODYWEIGHT)
    instructions = models.TextField(blank=True)
    is_compound = models.BooleanField(default=False)
    met_value = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=4.0,
        help_text="MET value for cardio calorie estimation.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
