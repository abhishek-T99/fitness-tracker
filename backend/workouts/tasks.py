"""Celery tasks for the workouts app.

Heavy post-save work (achievement evaluation, XP awarding, PR detection) is
dispatched here so HTTP write paths return immediately. Each piece scans
some portion of the user's workout history, which is O(history) and not
something the request should block on.
"""
from __future__ import annotations

import logging

from celery import shared_task

from .models import ExerciseSet, Workout

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def process_completed_workout(workout_id: int, *, award_xp: bool) -> None:
    """Run achievement eval + (optionally) XP awarding for a completed workout.

    Called from ``workouts.signals.on_workout_saved`` via ``.delay()``.
    ``award_xp=False`` skips XP for the workout-creation path so we don't
    award XP on backfilled imports (Strava, intervals, etc.).
    """
    try:
        workout = (
            Workout.objects
            .select_related("user")
            .get(pk=workout_id)
        )
    except Workout.DoesNotExist:
        logger.warning("process_completed_workout: workout %s not found", workout_id)
        return

    if workout.status != Workout.Status.COMPLETED:
        return

    # Local imports avoid circular module load at task-registration time.
    from achievements.services import evaluate_after_workout

    evaluate_after_workout(workout)

    if award_xp:
        _award_workout_xp(workout)
        _award_pr_xp(workout)


def _award_workout_xp(workout: Workout) -> None:
    """Award base workout-completion XP, scaled by duration and volume."""
    try:
        from levels.services import award_xp, increment_challenge
    except ImportError:
        return

    # Idempotency: skip if we've already recorded XP for this workout.
    from levels.models import XPTransaction
    already = XPTransaction.objects.filter(
        user=workout.user,
        source_type="workout",
        source_id=workout.id,
    ).exists()
    if already:
        return

    duration = workout.duration_min or 0
    volume = sum(
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
        best_this = 0.0
        for s in we.sets.filter(is_warmup=False, completed=True, reps__gt=0, weight__isnull=False):
            orm = float(s.weight) * (1 + int(s.reps) / 30)
            if orm > best_this:
                best_this = orm

        if best_this <= 0:
            continue

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
