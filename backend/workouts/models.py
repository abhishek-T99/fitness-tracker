from django.conf import settings
from django.db import models


class Routine(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routines")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    estimated_duration_min = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order", "-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_routine_name_per_user"),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class RoutineExercise(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name="items")
    exercise = models.ForeignKey("exercises.Exercise", on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)
    target_sets = models.PositiveIntegerField(default=3)
    target_reps = models.PositiveIntegerField(blank=True, null=True)
    target_weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    target_duration_sec = models.PositiveIntegerField(blank=True, null=True)
    rest_sec = models.PositiveIntegerField(default=60)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["order", "id"]


class Workout(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workouts")
    routine = models.ForeignKey(
        Routine, on_delete=models.SET_NULL, blank=True, null=True, related_name="workouts"
    )
    name = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(blank=True, null=True)
    duration_min = models.PositiveIntegerField(blank=True, null=True)
    calories_burned = models.PositiveIntegerField(blank=True, null=True)
    perceived_exertion = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="1-10 RPE"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    # Populated when a workout is imported from a third-party platform
    source = models.CharField(max_length=32, blank=True)       # e.g. "intervals", "strava"
    distance_km = models.DecimalField(max_digits=7, decimal_places=3, blank=True, null=True)
    avg_hr_bpm = models.PositiveSmallIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.name or 'Workout'} on {self.started_at:%Y-%m-%d}"

    @property
    def total_volume(self):
        total = 0
        for entry in self.exercises.all():
            for s in entry.sets.all():
                if s.weight and s.reps:
                    total += float(s.weight) * s.reps
        return round(total, 2)


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="exercises")
    exercise = models.ForeignKey("exercises.Exercise", on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["order", "id"]


class ExerciseSet(models.Model):
    workout_exercise = models.ForeignKey(
        WorkoutExercise, on_delete=models.CASCADE, related_name="sets"
    )
    set_number = models.PositiveIntegerField(default=1)
    reps = models.PositiveIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    duration_sec = models.PositiveIntegerField(blank=True, null=True)
    distance_m = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    rpe = models.PositiveSmallIntegerField(blank=True, null=True)
    is_warmup = models.BooleanField(default=False)
    completed = models.BooleanField(default=True)

    class Meta:
        ordering = ["set_number", "id"]
