"""
Calorie estimation for workouts.

Method: MET (Metabolic Equivalent of Task) — the same standard used by
ACSM, WHO, and every major fitness app.

  calories = MET × body_weight_kg × active_hours

For strength training, we derive "active hours" from the sets/reps/duration
stored on ExerciseSet because the workout duration_min includes warm-up,
transitions, and rest — which inflate the estimate if used naively.

Accuracy: ±15-20 % — comparable to wrist-based HR monitors.
The main variable we can't measure is individual metabolic rate.

Override policy
───────────────
Auto-calculation only runs when workout.calories_burned is None.
If the user (or a device sync) has already set it, we never overwrite it.
The `recalculate_calories` viewset action lets the user reset to auto.
"""
import logging

logger = logging.getLogger(__name__)

# Seconds a lifter spends under tension per rep for each exercise type.
_SECS_PER_REP_COMPOUND  = 3    # e.g. squat, bench, deadlift
_SECS_PER_REP_ISOLATION = 2    # e.g. curl, lateral raise

# Fraction of active MET applied during rest periods.
# Resting burns ~1 MET; we model it as 25 % of the active MET as a
# conservative mid-point between sitting still and walking.
_REST_MET_FRACTION = 0.25

# Assumed rest between sets when ExerciseSet.rest_sec is not stored.
_DEFAULT_REST_SEC = 90

# Fallback MET when an exercise has no met_value.
_DEFAULT_MET = 4.5

# Fallback body weight when neither measurements nor profile give us one.
_DEFAULT_WEIGHT_KG = 75.0


# ── Body weight lookup ────────────────────────────────────────────────────────

def get_user_weight_kg(user) -> float:
    """
    Body weight priority:
      1. Most recent BodyMeasurement with weight_kg set
      2. BMI 22 × (height from profile)²  — a neutral healthy-weight estimate
      3. Hard fallback: 75 kg
    """
    from measurements.models import BodyMeasurement

    latest = (
        BodyMeasurement.objects
        .filter(user=user, weight_kg__isnull=False)
        .order_by("-recorded_at")
        .values_list("weight_kg", flat=True)
        .first()
    )
    if latest:
        return float(latest)

    height_cm = getattr(getattr(user, "profile", None), "height_cm", None)
    if height_cm:
        h_m = float(height_cm) / 100
        return round(22.0 * h_m * h_m, 1)

    return _DEFAULT_WEIGHT_KG


# ── Per-set calorie math ──────────────────────────────────────────────────────

def _kcal_for_set(exercise_set, met: float, weight_kg: float, is_compound: bool) -> float:
    """Return kcal burned during one completed set (active time only)."""

    # 1. Cardio set with explicit duration (e.g. a 30-min run segment)
    if exercise_set.duration_sec:
        active_hours = exercise_set.duration_sec / 3600
        return met * weight_kg * active_hours

    # 2. Strength set: reps × time-under-tension
    if exercise_set.reps:
        secs = exercise_set.reps * (_SECS_PER_REP_COMPOUND if is_compound else _SECS_PER_REP_ISOLATION)
        return met * weight_kg * (secs / 3600)

    # 3. Distance-based set (e.g. a single 5 km run logged as distance_m)
    if exercise_set.distance_m:
        # Assume a moderate running pace of ~5 min/km
        est_sec = (exercise_set.distance_m / 1000) * 300
        return met * weight_kg * (est_sec / 3600)

    return 0.0


# ── Main estimation function ──────────────────────────────────────────────────

def estimate_calories(workout) -> int | None:
    """
    Estimate total kcal burned for a completed workout.

    Returns an integer (rounded) or None if the workout has no usable data.
    Only call this when workout.calories_burned is None — callers are
    responsible for the override policy.
    """
    weight_kg = get_user_weight_kg(workout.user)
    total     = 0.0
    has_data  = False

    exercises = list(
        workout.exercises
        .select_related("exercise")
        .prefetch_related("sets")
    )

    for we in exercises:
        ex          = we.exercise
        met         = float(ex.met_value) if ex.met_value else _DEFAULT_MET
        is_compound = ex.is_compound

        completed = [s for s in we.sets.all() if s.completed]
        if not completed:
            continue

        has_data = True
        n_sets   = len(completed)

        # Active calories (time under tension / cardio duration)
        for s in completed:
            total += _kcal_for_set(s, met, weight_kg, is_compound)

        # Rest calories: n_sets rest periods at a reduced MET
        rest_hours = (n_sets * _DEFAULT_REST_SEC) / 3600
        total += (met * _REST_MET_FRACTION) * weight_kg * rest_hours

    # Fallback: no set data but we know the workout duration
    if not has_data and workout.duration_min:
        total = _DEFAULT_MET * weight_kg * (workout.duration_min / 60)
        has_data = True

    if not has_data or total <= 0:
        return None

    return max(1, round(total))


# ── Public entry point ────────────────────────────────────────────────────────

def auto_calculate_calories(workout) -> bool:
    """
    Estimate and save calories_burned if it isn't already set.

    Returns True if the field was updated, False if skipped.
    Uses update() to avoid re-triggering post_save signals.
    """
    if workout.calories_burned is not None:
        return False   # user or device has already set this — respect it

    estimate = estimate_calories(workout)
    if estimate is None:
        return False

    from .models import Workout as _W
    _W.objects.filter(pk=workout.pk).update(calories_burned=estimate)
    workout.calories_burned = estimate   # keep in-memory object in sync
    logger.debug("Auto-calculated %d kcal for workout %s", estimate, workout.pk)
    return True
