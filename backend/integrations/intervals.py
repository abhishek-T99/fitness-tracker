"""
Intervals.icu REST API client.

Authentication: HTTP Basic Auth with username="API_KEY" and
password=<user's api key from their Intervals.icu profile settings>.

Athlete IDs look like "i12345" (the "i" prefix is required).

API reference: https://intervals.icu/api-docs.html
"""
import math
import logging
from datetime import datetime, timezone as dt_timezone

import requests

logger = logging.getLogger(__name__)

BASE = "https://intervals.icu/api/v1"

# Intervals.icu sport type → human label used in workout name / notes
SPORT_LABELS = {
    "Run": "Run",
    "Ride": "Ride",
    "VirtualRide": "Virtual Ride",
    "VirtualRun": "Virtual Run",
    "Swim": "Swim",
    "Walk": "Walk",
    "Hike": "Hike",
    "WeightTraining": "Weight Training",
    "Workout": "Workout",
    "Yoga": "Yoga",
    "Crossfit": "CrossFit",
    "Elliptical": "Elliptical",
    "StairStepper": "Stair Stepper",
    "RockClimbing": "Rock Climbing",
    "Rowing": "Rowing",
    "Soccer": "Soccer",
    "Tennis": "Tennis",
    "Basketball": "Basketball",
    "AlpineSki": "Alpine Ski",
    "NordicSki": "Nordic Ski",
    "Snowboard": "Snowboard",
    "Kayaking": "Kayaking",
    "Golf": "Golf",
    "Skateboard": "Skateboard",
}


class IntervalsError(Exception):
    pass


def _auth(api_key: str):
    """Return the Basic Auth tuple expected by requests."""
    return ("API_KEY", api_key)


def _get(path: str, api_key: str, **params) -> dict | list:
    resp = requests.get(
        f"{BASE}{path}",
        auth=_auth(api_key),
        params=params or None,
        timeout=15,
    )
    if resp.status_code == 401:
        raise IntervalsError("Invalid API key or athlete ID.")
    if resp.status_code == 404:
        raise IntervalsError(f"Resource not found: {path}")
    if not resp.ok:
        raise IntervalsError(f"Intervals.icu API error {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def verify_credentials(athlete_id: str, api_key: str) -> dict:
    """
    Verify credentials by fetching the athlete profile.
    Returns the athlete dict on success; raises IntervalsError on failure.
    """
    return _get(f"/athlete/{athlete_id}", api_key)


def get_activities(
    athlete_id: str,
    api_key: str,
    oldest: str | None = None,
    newest: str | None = None,
) -> list:
    """
    Fetch a list of activities for the athlete.

    oldest / newest: ISO date strings "YYYY-MM-DD" (optional).
    Returns a list of activity summary dicts.
    """
    params = {}
    if oldest:
        params["oldest"] = oldest
    if newest:
        params["newest"] = newest
    return _get(f"/athlete/{athlete_id}/activities", api_key, **params)


def get_activity(athlete_id: str, activity_id: int | str, api_key: str) -> dict:
    """Fetch a single activity by its Intervals.icu ID."""
    return _get(f"/activity/{activity_id}", api_key)


def get_wellness(
    athlete_id: str,
    api_key: str,
    oldest: str | None = None,
    newest: str | None = None,
) -> list:
    """
    Fetch daily wellness entries (steps, resting HR, HRV, sleep score, weight).

    oldest / newest: ISO date strings "YYYY-MM-DD".
    Returns a list of wellness dicts.
    """
    params = {}
    if oldest:
        params["oldest"] = oldest
    if newest:
        params["newest"] = newest
    return _get(f"/athlete/{athlete_id}/wellness", api_key, **params)


def map_activity_to_workout(activity: dict) -> dict:
    """
    Convert an Intervals.icu activity dict to Workout model kwargs.

    Intervals.icu activity fields we use:
      id, name, type, start_date_local, moving_time, elapsed_time,
      distance, average_heartrate, calories, icu_training_load
    """
    from django.utils.dateparse import parse_datetime

    sport = activity.get("type", "Workout")
    label = SPORT_LABELS.get(sport, sport)

    activity_name = (activity.get("name") or "").strip()
    name = activity_name or f"{label} via Intervals.icu"

    # Prefer moving_time; fall back to elapsed_time
    duration_sec = activity.get("moving_time") or activity.get("elapsed_time") or 0
    duration_min = math.ceil(duration_sec / 60) if duration_sec else None

    distance_m = activity.get("distance")  # metres
    distance_km = round(distance_m / 1000, 3) if distance_m else None

    avg_hr = activity.get("average_heartrate")
    calories = activity.get("calories")

    # start_date_local is "YYYY-MM-DDTHH:MM:SS" without tz — treat as UTC
    raw_start = activity.get("start_date_local") or activity.get("start_date", "")
    if raw_start and "+" not in raw_start and raw_start[-1] != "Z":
        raw_start += "Z"
    started_at = parse_datetime(raw_start)

    notes_parts = [f"Imported from Intervals.icu · {label}"]
    if activity.get("icu_training_load"):
        notes_parts.append(f"Training load: {activity['icu_training_load']:.0f}")

    return {
        "name": name[:120],
        "notes": " · ".join(notes_parts),
        "started_at": started_at,
        "ended_at": started_at,
        "duration_min": duration_min,
        "calories_burned": int(calories) if calories else None,
        "distance_km": distance_km,
        "avg_hr_bpm": round(avg_hr) if avg_hr else None,
        "source": "intervals",
        "status": "completed",
    }
