"""Signal hooks for workouts — caching + achievement triggers + calorie estimation."""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ExerciseSet, Workout, WorkoutExercise


def _invalidate_workout_stats(user_id: int) -> None:
    cache.delete_many([f"workout_stats:{user_id}", f"streak:{user_id}"])


@receiver(post_save, sender=Workout)
def on_workout_saved(sender, instance, created, **kwargs):
    _invalidate_workout_stats(instance.user_id)
    if instance.status != Workout.Status.COMPLETED:
        return
    from achievements.tasks import evaluate_workout_achievements
    evaluate_workout_achievements.delay(instance.id)

    # Auto-estimate calories on save (e.g. session complete, import from device)
    # Only runs when calories_burned is None — never overwrites user/device values.
    if instance.calories_burned is None:
        from .services import auto_calculate_calories
        auto_calculate_calories(instance)


@receiver(post_delete, sender=Workout)
def on_workout_deleted(sender, instance, **kwargs):
    _invalidate_workout_stats(instance.user_id)


@receiver([post_save, post_delete], sender=WorkoutExercise)
def on_workout_exercise_changed(sender, instance, **kwargs):
    _invalidate_workout_stats(instance.workout.user_id)


@receiver([post_save, post_delete], sender=ExerciseSet)
def on_set_changed(sender, instance, **kwargs):
    workout = instance.workout_exercise.workout
    _invalidate_workout_stats(workout.user_id)

    # Re-estimate calories whenever a set is added/updated/removed.
    # We re-fetch calories_burned so we see the current DB value, not a
    # potentially stale in-memory copy from earlier in the request cycle.
    if workout.status == Workout.Status.COMPLETED:
        workout.refresh_from_db(fields=["calories_burned"])
        if workout.calories_burned is None:
            from .services import auto_calculate_calories
            auto_calculate_calories(workout)
