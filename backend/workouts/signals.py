"""Signal hooks for workouts — caching + achievement triggers."""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ExerciseSet, Workout, WorkoutExercise


def _invalidate_workout_stats(user_id: int) -> None:
    """Drop cached stats for a user. Called from save/delete signals."""
    cache.delete_many(
        [
            f"workout_stats:{user_id}",
            f"streak:{user_id}",
        ]
    )


@receiver(post_save, sender=Workout)
def on_workout_saved(sender, instance, created, **kwargs):
    _invalidate_workout_stats(instance.user_id)
    if instance.status != Workout.Status.COMPLETED:
        return
    # Local import keeps Celery off the import path until needed.
    from achievements.tasks import evaluate_workout_achievements

    evaluate_workout_achievements.delay(instance.id)


@receiver(post_delete, sender=Workout)
def on_workout_deleted(sender, instance, **kwargs):
    _invalidate_workout_stats(instance.user_id)


@receiver([post_save, post_delete], sender=WorkoutExercise)
def on_workout_exercise_changed(sender, instance, **kwargs):
    _invalidate_workout_stats(instance.workout.user_id)


@receiver([post_save, post_delete], sender=ExerciseSet)
def on_set_changed(sender, instance, **kwargs):
    _invalidate_workout_stats(instance.workout_exercise.workout.user_id)
