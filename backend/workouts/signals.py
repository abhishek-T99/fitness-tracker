"""Signal hooks for workouts — cache invalidation + post-save dispatch."""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ExerciseSet, Workout, WorkoutExercise


def _invalidate_workout_stats(user_id: int) -> None:
    cache.delete_many([f"workout_stats:{user_id}", f"streak:{user_id}"])
    # Progress analytics keys use wildcard patterns — delete_pattern is provided
    # by django-redis and degrades silently (IGNORE_EXCEPTIONS=True) on plain caches.
    for prefix in ("progress:strength", "progress:volume", "progress:heatmap"):
        try:
            cache.delete_pattern(f"{prefix}:{user_id}:*")
        except AttributeError:
            pass  # non-redis backend in tests


@receiver(post_save, sender=Workout)
def on_workout_saved(sender, instance, created, **kwargs):
    _invalidate_workout_stats(instance.user_id)

    if instance.status != Workout.Status.COMPLETED:
        return

    # Auto-estimate calories synchronously — bounded by exercise count and
    # surfaced in the API response. Only runs when calories_burned is None;
    # never overwrites user/device-supplied values.
    if instance.calories_burned is None:
        from .services import auto_calculate_calories
        auto_calculate_calories(instance)

    # Achievements + XP scan the user's full workout history — push to Celery
    # so the API write returns immediately. award_xp=False on create matches
    # the previous guard: backfilled/imported workouts don't grant XP.
    from .tasks import process_completed_workout
    process_completed_workout.delay(instance.id, award_xp=not created)


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
    # Re-fetch calories_burned so we see the current DB value, not a
    # potentially stale in-memory copy from earlier in the request cycle.
    if workout.status == Workout.Status.COMPLETED:
        workout.refresh_from_db(fields=["calories_burned"])
        if workout.calories_burned is None:
            from .services import auto_calculate_calories
            auto_calculate_calories(workout)
