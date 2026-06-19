"""Aggregate all fitness data for a user over a date range."""
import logging
from datetime import date

from django.db.models import Avg, Max, Sum

logger = logging.getLogger(__name__)


def collect_report_data(user, period_start: date, period_end: date) -> dict:
    """Return a structured dict of fitness stats for the given period."""
    return {
        "user": user,
        "period_start": period_start,
        "period_end": period_end,
        "workout": _workout_stats(user, period_start, period_end),
        "streak": _streak_stats(user),
        "nutrition": _nutrition_stats(user, period_start, period_end),
        "body": _body_stats(user, period_start, period_end),
        "goals": _goal_stats(user, period_start, period_end),
        "achievements": _achievement_stats(user, period_start, period_end),
    }


# ── Workouts ──────────────────────────────────────────────────────────────────

def _workout_stats(user, period_start: date, period_end: date) -> dict:
    from workouts.models import Workout

    qs = Workout.objects.filter(
        user=user,
        status=Workout.Status.COMPLETED,
        started_at__date__gte=period_start,
        started_at__date__lte=period_end,
    )

    agg = qs.aggregate(
        total_minutes=Sum("duration_min"),
        total_calories=Sum("calories_burned"),
        longest_min=Max("duration_min"),
        avg_rpe=Avg("perceived_exertion"),
        total_distance=Sum("distance_km"),
    )

    total_minutes = agg["total_minutes"] or 0
    count = qs.count()

    # Volume = Σ weight × reps across all completed sets
    total_volume = 0.0
    for w in qs.prefetch_related("exercises__sets"):
        for ex in w.exercises.all():
            for s in ex.sets.filter(completed=True):
                if s.weight and s.reps:
                    total_volume += float(s.weight) * s.reps

    # Muscle group distribution (exercise category)
    from exercises.models import Exercise
    muscle_counts: dict[str, int] = {}
    for w in qs.prefetch_related("exercises__exercise"):
        for we in w.exercises.all():
            cat = getattr(we.exercise, "category", None) or "Other"
            muscle_counts[str(cat)] = muscle_counts.get(str(cat), 0) + 1
    top_muscles = sorted(muscle_counts.items(), key=lambda x: -x[1])[:3]

    weekly_goal = getattr(getattr(user, "profile", None), "weekly_workout_goal", 3) or 3

    # Determine the number of weeks in the period for goal comparison
    period_days = (period_end - period_start).days + 1
    weeks_in_period = max(period_days / 7, 1)
    goal_for_period = round(weekly_goal * weeks_in_period)

    return {
        "count": count,
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "total_calories": agg["total_calories"] or 0,
        "total_volume_kg": round(total_volume, 1),
        "longest_workout_min": agg["longest_min"] or 0,
        "avg_duration_min": round(total_minutes / count, 1) if count else 0,
        "avg_rpe": round(float(agg["avg_rpe"]), 1) if agg["avg_rpe"] else None,
        "total_distance_km": float(agg["total_distance"] or 0),
        "top_muscles": top_muscles,
        "weekly_goal": weekly_goal,
        "goal_for_period": goal_for_period,
        "goal_met": count >= goal_for_period,
    }


# ── Streaks ───────────────────────────────────────────────────────────────────

def _streak_stats(user) -> dict:
    from achievements.models import Streak

    try:
        streak = Streak.objects.get(user=user)
        return {
            "current": streak.current_days,
            "longest": streak.longest_days,
        }
    except Streak.DoesNotExist:
        return {"current": 0, "longest": 0}


# ── Nutrition ─────────────────────────────────────────────────────────────────

def _nutrition_stats(user, period_start: date, period_end: date) -> dict:
    from nutrition.models import Meal, WaterLog

    meals = Meal.objects.filter(
        user=user,
        consumed_at__date__gte=period_start,
        consumed_at__date__lte=period_end,
    ).prefetch_related("items__food")

    # Aggregate per calendar day
    daily: dict[str, dict] = {}
    for meal in meals:
        day = meal.consumed_at.date().isoformat()
        if day not in daily:
            daily[day] = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
        t = meal.totals
        for k in t:
            daily[day][k] = daily[day].get(k, 0.0) + t[k]

    logged_days = len(daily)
    period_days = (period_end - period_start).days + 1

    if logged_days:
        avg_calories = sum(d["calories"] for d in daily.values()) / logged_days
        avg_protein  = sum(d["protein_g"] for d in daily.values()) / logged_days
        avg_carbs    = sum(d["carbs_g"]   for d in daily.values()) / logged_days
        avg_fat      = sum(d["fat_g"]     for d in daily.values()) / logged_days
    else:
        avg_calories = avg_protein = avg_carbs = avg_fat = 0.0

    calorie_goal = getattr(getattr(user, "profile", None), "daily_calorie_goal", None)
    days_on_target = 0
    if calorie_goal:
        # Within 10 % above or below goal counts as on target
        lo, hi = calorie_goal * 0.90, calorie_goal * 1.10
        days_on_target = sum(1 for d in daily.values() if lo <= d["calories"] <= hi)

    # Water
    water_qs = WaterLog.objects.filter(
        user=user,
        logged_at__date__gte=period_start,
        logged_at__date__lte=period_end,
    )
    daily_water: dict[str, int] = {}
    for log in water_qs:
        day = log.logged_at.date().isoformat()
        daily_water[day] = daily_water.get(day, 0) + log.amount_ml
    avg_water_ml = (
        sum(daily_water.values()) / len(daily_water) if daily_water else 0.0
    )

    return {
        "logged_days": logged_days,
        "period_days": period_days,
        "avg_calories": round(avg_calories, 1),
        "avg_protein_g": round(avg_protein, 1),
        "avg_carbs_g": round(avg_carbs, 1),
        "avg_fat_g": round(avg_fat, 1),
        "calorie_goal": calorie_goal,
        "days_on_target": days_on_target,
        "avg_water_ml": round(avg_water_ml),
        "avg_water_l": round(avg_water_ml / 1000, 1),
    }


# ── Body composition ──────────────────────────────────────────────────────────

def _body_stats(user, period_start: date, period_end: date) -> dict:
    from measurements.models import BodyMeasurement

    measurements = BodyMeasurement.objects.filter(
        user=user,
        recorded_at__gte=period_start,
        recorded_at__lte=period_end,
    ).order_by("recorded_at")

    profile = getattr(user, "profile", None)
    units = getattr(profile, "units", "metric")

    if not measurements.exists():
        return {"units": units, "weight_start": None, "weight_end": None, "weight_change": None, "bmi_start": None, "bmi_end": None}

    first_m = measurements.first()
    last_m  = measurements.last()

    def _weight(m):
        if not m.weight_kg:
            return None
        w = float(m.weight_kg)
        return round(w * 2.20462, 1) if units == "imperial" else round(w, 1)

    weight_start = _weight(first_m)
    weight_end   = _weight(last_m)
    weight_change = (
        round(weight_end - weight_start, 1)
        if weight_start is not None and weight_end is not None
        else None
    )

    return {
        "units": units,
        "weight_unit": "lb" if units == "imperial" else "kg",
        "weight_start": weight_start,
        "weight_end": weight_end,
        "weight_change": weight_change,
        "bmi_start": first_m.bmi,
        "bmi_end": last_m.bmi,
    }


# ── Goals ─────────────────────────────────────────────────────────────────────

def _goal_stats(user, period_start: date, period_end: date) -> dict:
    from goals.models import Goal

    active_goals = Goal.objects.filter(user=user, status=Goal.Status.ACTIVE)
    achieved_in_period = Goal.objects.filter(
        user=user,
        status=Goal.Status.ACHIEVED,
        updated_at__date__gte=period_start,
        updated_at__date__lte=period_end,
    )

    active_snapshot = [
        {
            "title": g.title,
            "goal_type": g.goal_type,
            "progress_percent": g.progress_percent,
            "target_value": float(g.target_value),
            "current_value": float(g.current_value),
            "unit": g.unit,
        }
        for g in active_goals[:6]
    ]

    avg_progress = (
        round(sum(g["progress_percent"] for g in active_snapshot) / len(active_snapshot), 1)
        if active_snapshot
        else 0.0
    )

    return {
        "active_count": active_goals.count(),
        "active_goals": active_snapshot,
        "avg_progress_percent": avg_progress,
        "achieved_in_period": achieved_in_period.count(),
        "achieved_titles": [g.title for g in achieved_in_period[:3]],
    }


# ── Achievements ──────────────────────────────────────────────────────────────

def _achievement_stats(user, period_start: date, period_end: date) -> dict:
    from achievements.models import UserAchievement

    new_ua = UserAchievement.objects.filter(
        user=user,
        unlocked_at__date__gte=period_start,
        unlocked_at__date__lte=period_end,
    ).select_related("achievement")

    total_count = UserAchievement.objects.filter(user=user).count()

    return {
        "new_count": new_ua.count(),
        "new_badges": [ua.achievement.name for ua in new_ua[:6]],
        "total_count": total_count,
    }
