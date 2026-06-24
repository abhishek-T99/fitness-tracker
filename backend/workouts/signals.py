"""Signal hooks for workouts — caching + achievement triggers + calorie estimation + XP."""
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
    from achievements.services import evaluate_after_workout
    evaluate_after_workout(instance)

    # Auto-estimate calories on save (e.g. session complete, import from device)
    # Only runs when calories_burned is None — never overwrites user/device values.
    if instance.calories_burned is None:
        from .services import auto_calculate_calories
        auto_calculate_calories(instance)

    # Award XP for completing a workout — only on the transition to COMPLETED
    # (created=False + status=COMPLETED guards against double-awarding).
    if created:
        return  # newly created workouts are never already COMPLETED via session save
    _award_workout_xp(instance)
    _award_pr_xp(instance)


def _award_workout_xp(workout: Workout) -> None:
    """Award base workout-completion XP, scaled by duration and volume."""
    try:
        from levels.services import award_xp, increment_challenge
    except ImportError:
        return

    # Avoid double-awarding: check if we already have a transaction for this workout
    from levels.models import XPTransaction
    already = XPTransaction.objects.filter(
        user=workout.user,
        source_type="workout",
        source_id=workout.id,
    ).exists()
    if already:
        return

    duration = workout.duration_min or 0
    volume   = float(
        ExerciseSet.objects.filter(
            workout_exercise__workout=workout,
            completed=True,
            weight__isnull=False,
            weight__gt=0,
            reps__gt=0,
        ).values_list("weight", "reps")
        .__class__(  # keep as queryset; compute sum below
        )
    ) if False else sum(
        float(w) * r
        for w, r in ExerciseSet.objects.filter(
            workout_exercise__workout=workout,
            completed=True,
            weight__isnull=False,
            weight__gt=0,
            reps__gt=0,
        ).values_list("weight", "reps")
    )

    base_xp = 100 + int(duration * 2) + int(volume * 0.05)
    award_xp(
        workout.user, base_xp,
        f"Completed workout: {workout.name or 'Workout'}",
        "workout", workout.id,
    )
    increment_challenge(workout.user, "complete_workouts")


def _award_pr_xp(workout: Workout) -> None:
    """Award 250 XP for each new personal record (1RM) set in this workout."""
    try:
        from levels.services import award_xp, increment_challenge
    except ImportError:
        return

    for we in workout.exercises.prefetch_related("sets", "exercise").all():
        # Best Epley 1RM this session
        best_this = 0.0
        for s in we.sets.filter(is_warmup=False, completed=True, reps__gt=0, weight__isnull=False):
            orm = float(s.weight) * (1 + int(s.reps) / 30)
            if orm > best_this:
                best_this = orm

        if best_this <= 0:
            continue

        # Best Epley 1RM in all prior completed workouts for this exercise
        prev_best = 0.0
        for w, r in ExerciseSet.objects.filter(
            workout_exercise__exercise=we.exercise,
            workout_exercise__workout__user=workout.user,
            workout_exercise__workout__status=Workout.Status.COMPLETED,
            is_warmup=False,
            completed=True,
            reps__gt=0,
            weight__isnull=False,
        ).exclude(
            workout_exercise__workout=workout
        ).values_list("weight", "reps"):
            orm = float(w) * (1 + int(r) / 30)
            if orm > prev_best:
                prev_best = orm

        if best_this > prev_best:
            award_xp(
                workout.user, 250,
                f"New PR — {we.exercise.name}",
                "personal_record", workout.id,
            )
            increment_challenge(workout.user, "record_pr")


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
