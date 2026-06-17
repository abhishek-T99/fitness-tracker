"""
XP engine for the leveling system.

Public surface:
    xp_for_level(n)            → total XP threshold for level n
    calculate_level(total_xp)  → current level integer
    get_tier(level)            → tier string
    award_xp(...)              → (xp_awarded, leveled_up)
    increment_challenge(...)   → update weekly challenge progress
    detect_athlete_class(user) → athlete class string
"""
from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal


# ── Level / XP maths ─────────────────────────────────────────────────────────

def xp_for_level(n: int) -> int:
    """Total XP required to *reach* level n (1-indexed)."""
    if n <= 1:
        return 0
    return int(100 * (n - 1) ** 1.6)


def calculate_level(total_xp: int) -> int:
    """Binary-search the level for a given total_xp value."""
    lo, hi = 1, 500
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if xp_for_level(mid) <= total_xp:
            lo = mid
        else:
            hi = mid - 1
    return lo


def get_tier(level: int) -> str:
    if level >= 100: return "immortal"
    if level >= 75:  return "elite"
    if level >= 50:  return "legend"
    if level >= 35:  return "warrior"
    if level >= 20:  return "athlete"
    if level >= 10:  return "amateur"
    return "rookie"


def get_streak_multiplier(user) -> float:
    """Read current streak from cache and return the XP multiplier."""
    from django.core.cache import cache
    from fitness_tracker import cache_keys

    streak_data = cache.get(cache_keys.streak(user.id)) or {}
    current = streak_data.get("current", 0)
    if current >= 30: return 2.0
    if current >= 14: return 1.5
    if current >= 7:  return 1.25
    if current >= 3:  return 1.1
    return 1.0


# ── Core award function ───────────────────────────────────────────────────────

def award_xp(
    user,
    base_amount: int,
    reason: str,
    source_type: str,
    source_id: int | None = None,
) -> tuple[int, bool]:
    """
    Award XP to a user, applying the current streak multiplier.

    Returns (xp_awarded, leveled_up).
    Uses select_for_update so concurrent calls don't double-count.
    """
    from django.db import transaction
    from .models import UserLevel, XPTransaction

    multiplier   = get_streak_multiplier(user)
    final_amount = max(1, int(base_amount * multiplier))

    with transaction.atomic():
        user_level, _ = UserLevel.objects.select_for_update().get_or_create(user=user)
        old_level     = user_level.level

        XPTransaction.objects.create(
            user        = user,
            amount      = final_amount,
            base_amount = base_amount,
            multiplier  = Decimal(str(multiplier)),
            reason      = reason,
            source_type = source_type,
            source_id   = source_id,
        )

        user_level.total_xp += final_amount
        new_level            = calculate_level(user_level.total_xp)
        new_tier             = get_tier(new_level)
        user_level.level     = new_level
        user_level.tier      = new_tier
        user_level.save(update_fields=["total_xp", "level", "tier", "updated_at"])

    return final_amount, new_level > old_level


# ── Challenge progress ────────────────────────────────────────────────────────

def increment_challenge(user, challenge_type: str, increment: int = 1) -> None:
    """
    Advance the user's progress on any active challenge of the given type.
    Automatically awards challenge XP on completion.
    """
    from django.db.models import F
    from django.utils import timezone
    from .models import WeeklyChallenge, UserWeeklyChallenge

    today      = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())  # Monday

    for challenge in WeeklyChallenge.objects.filter(
        week_start=week_start, challenge_type=challenge_type
    ):
        uc, _ = UserWeeklyChallenge.objects.get_or_create(user=user, challenge=challenge)
        if uc.completed:
            continue

        UserWeeklyChallenge.objects.filter(pk=uc.pk).update(
            current_value=F("current_value") + increment
        )
        uc.refresh_from_db()

        if uc.current_value >= challenge.target_value:
            UserWeeklyChallenge.objects.filter(pk=uc.pk).update(
                completed=True,
                completed_at=timezone.now(),
            )
            award_xp(
                user, challenge.xp_reward,
                f"Challenge: {challenge.description}",
                "challenge", challenge.id,
            )


# ── Athlete class detection ───────────────────────────────────────────────────

def detect_athlete_class(user) -> str:
    """
    Analyse the last 4 weeks of completed workouts to assign an athlete class.
    Returns a UserLevel.AthleteClass value string.
    """
    from django.db.models import Avg
    from django.utils import timezone
    from workouts.models import Workout, ExerciseSet

    four_weeks_ago = timezone.now() - timedelta(weeks=4)
    workouts = Workout.objects.filter(
        user=user,
        status=Workout.Status.COMPLETED,
        started_at__gte=four_weeks_ago,
    )
    count = workouts.count()

    if count < 3:
        return "rookie"

    # Cardio-dominant
    cardio_count = (
        workouts.filter(exercises__exercise__category="cardio").distinct().count()
    )
    if count and cardio_count / count >= 0.6:
        return "road_warrior"

    # Very high frequency → CrossFit / HIIT style
    if count >= 20:
        return "fire_breather"

    # Average working-set weight
    avg_weight = (
        ExerciseSet.objects.filter(
            workout_exercise__workout__in=workouts,
            weight__isnull=False,
            weight__gt=0,
            is_warmup=False,
            completed=True,
        ).aggregate(avg=Avg("weight"))["avg"] or 0
    )
    if float(avg_weight) >= 70:
        return "iron_warrior"

    # Wellness: consistent nutrition + measurement logging
    try:
        from nutrition.models import Meal
        from measurements.models import BodyMeasurement

        meals = Meal.objects.filter(user=user, consumed_at__gte=four_weeks_ago).count()
        msmts = BodyMeasurement.objects.filter(
            user=user, recorded_at__gte=four_weeks_ago.date()
        ).count()
        if meals >= 40 and msmts >= 2:
            return "wellness_champion"
    except Exception:
        pass

    return "sculptor"


# ── Weekly challenge templates ────────────────────────────────────────────────

CHALLENGE_TEMPLATES = [
    {"type": "complete_workouts", "options": [(3, 200), (4, 250), (5, 300)]},
    {"type": "log_meals",         "options": [(5, 150), (6, 180), (7, 200)]},
    {"type": "log_water",         "options": [(5, 100), (7, 130), (7, 150)]},
    {"type": "log_measurement",   "options": [(1, 100), (2, 150), (3, 200)]},
    {"type": "record_pr",         "options": [(1, 200), (2, 300), (3, 400)]},
]

CHALLENGE_DESCRIPTIONS = {
    "complete_workouts": "Complete {n} workout{s} this week",
    "log_meals":         "Log meals for {n} day{s} this week",
    "log_water":         "Log water intake for {n} day{s} this week",
    "log_measurement":   "Record {n} body measurement{s} this week",
    "record_pr":         "Set {n} new personal record{s} this week",
}


def generate_weekly_challenges(week_start) -> list:
    """
    Pick 3 distinct challenge types for the given week and create
    WeeklyChallenge objects.  Idempotent — skips types already created.
    """
    from .models import WeeklyChallenge

    existing_types = set(
        WeeklyChallenge.objects.filter(week_start=week_start)
        .values_list("challenge_type", flat=True)
    )

    pool = [t for t in CHALLENGE_TEMPLATES if t["type"] not in existing_types]
    selected = random.sample(pool, min(3, len(pool)))
    created  = []

    for tmpl in selected:
        target, reward = random.choice(tmpl["options"])
        s    = "s" if target != 1 else ""
        desc = CHALLENGE_DESCRIPTIONS[tmpl["type"]].format(n=target, s=s)
        obj  = WeeklyChallenge.objects.create(
            week_start     = week_start,
            challenge_type = tmpl["type"],
            target_value   = target,
            xp_reward      = reward,
            description    = desc,
        )
        created.append(obj)

    return created
