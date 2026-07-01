"""Central registry of cache keys + TTLs.

Keeping them here means invalidation signals and read paths can't drift.
"""

EXERCISE_LIST = "exercises:catalog:v1"
EXERCISE_LIST_TTL = 60 * 60 * 24  # 24h — static catalog, invalidated on Exercise save.

# Per-querystring exercise list cache (used by the read-only ViewSet).
# Each variant is keyed by an md5 of sorted query params.
EXERCISE_LIST_VARIANT_PREFIX = "exercises:list:"
EXERCISE_LIST_VARIANT_TTL = 60 * 60 * 24  # 24h — same invalidation as the catalog.

ACHIEVEMENT_CATALOG = "achievements:catalog:v1"
ACHIEVEMENT_CATALOG_TTL = 60 * 60 * 24

PUBLIC_FOODS = "nutrition:foods:public:v1"
PUBLIC_FOODS_TTL = 60 * 60 * 6


def workout_stats(user_id: int) -> str:
    return f"workout_stats:{user_id}"


WORKOUT_STATS_TTL = 60 * 5  # 5 min, invalidated on Workout writes anyway.


def nutrition_summary(user_id: int, date_iso: str) -> str:
    return f"nutrition:summary:{user_id}:{date_iso}"


NUTRITION_SUMMARY_TTL = 60 * 2  # short — invalidated on meal/water writes too.


def nutrition_version(user_id: int) -> str:
    # Monotonic counter bumped on any Meal/MealItem/WaterLog write. Range-summary
    # keys embed the current version so writes atomically invalidate every cached
    # range without needing to scan or track individual keys.
    return f"nutrition:ver:{user_id}"


def nutrition_range_summary(
    user_id: int, start_iso: str, end_iso: str, granularity: str, version: int
) -> str:
    return (
        f"nutrition:range:{user_id}:{version}:{granularity}:{start_iso}:{end_iso}"
    )


NUTRITION_RANGE_SUMMARY_TTL = 60 * 10  # 10 min — versioned, so stale entries just age out.


def streak(user_id: int) -> str:
    return f"streak:{user_id}"


STREAK_TTL = 60 * 5


# ── Progress analytics ────────────────────────────────────────────────────────
# All progress keys share the prefix pattern "progress:<type>:<user_id>:..."
# so a single delete_pattern("progress:*:<user_id>:*") clears them all.

def strength_history(user_id: int, exercise_id: int, days: int) -> str:
    return f"progress:strength:{user_id}:{exercise_id}:{days}"


def volume_by_muscle(user_id: int, weeks: int) -> str:
    return f"progress:volume:{user_id}:{weeks}"


def activity_heatmap(user_id: int, days: int) -> str:
    return f"progress:heatmap:{user_id}:{days}"


def body_composition(user_id: int, days: int) -> str:
    return f"progress:body_comp:{user_id}:{days}"


PROGRESS_TTL = 60 * 5          # 5 min — same as workout_stats
BODY_COMP_TTL = 60 * 2         # 2 min — same as nutrition_summary
