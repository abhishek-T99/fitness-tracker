"""
Strava OAuth2 + REST API client.

All network calls are isolated here so tests can mock at the module boundary.
"""
import math
from datetime import datetime, timezone as dt_timezone

import requests
from django.conf import settings

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"
STRAVA_WEBHOOK_BASE = "https://www.strava.com/api/v3/push_subscriptions"

# Strava activity type → human-readable name we use as the workout name prefix
ACTIVITY_TYPE_LABELS = {
    "Run": "Run",
    "Ride": "Ride",
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
    "Kayaking": "Kayaking",
    "Rowing": "Rowing",
    "Golf": "Golf",
    "Skateboard": "Skateboard",
    "Soccer": "Soccer",
    "Tennis": "Tennis",
    "Basketball": "Basketball",
}


class StravaError(Exception):
    pass


def get_auth_url(redirect_uri: str, state: str) -> str:
    """Return the Strava authorization URL to redirect the user to."""
    params = (
        f"client_id={settings.STRAVA_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&approval_prompt=auto"
        f"&scope=read,activity:read_all,profile:read_all"
        f"&state={state}"
    )
    return f"{STRAVA_AUTH_URL}?{params}"


def exchange_code(code: str) -> dict:
    """Exchange an authorization code for tokens. Returns the full token dict."""
    resp = requests.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    data = resp.json()
    if resp.status_code != 200 or "access_token" not in data:
        raise StravaError(data.get("message", "Token exchange failed"))
    return data


def refresh_access_token(refresh_token: str) -> dict:
    """Use a refresh token to obtain a new access token."""
    resp = requests.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": settings.STRAVA_CLIENT_ID,
            "client_secret": settings.STRAVA_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    data = resp.json()
    if resp.status_code != 200 or "access_token" not in data:
        raise StravaError(data.get("message", "Token refresh failed"))
    return data


def get_activity(access_token: str, activity_id: int) -> dict:
    """Fetch a single Strava activity by ID."""
    resp = requests.get(
        f"{STRAVA_API_BASE}/activities/{activity_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if resp.status_code != 200:
        raise StravaError(f"Strava API returned {resp.status_code}")
    return resp.json()


def ensure_fresh_token(oauth_token) -> str:
    """
    Return a valid access token, refreshing it first if expired.
    Mutates the OAuthToken instance in-place and saves.
    """
    from django.utils import timezone as dj_timezone

    if oauth_token.is_expired():
        data = refresh_access_token(oauth_token.refresh_token)
        oauth_token.access_token = data["access_token"]
        oauth_token.refresh_token = data.get("refresh_token", oauth_token.refresh_token)
        oauth_token.expires_at = datetime.fromtimestamp(
            data["expires_at"], tz=dt_timezone.utc
        )
        oauth_token.save(update_fields=["access_token", "refresh_token", "expires_at"])
    return oauth_token.access_token


def map_activity_to_workout(activity: dict) -> dict:
    """
    Convert a Strava activity dict to the kwargs needed to create a Workout.

    Returns a dict with keys matching Workout model fields.
    """
    from django.utils.dateparse import parse_datetime

    started_at = parse_datetime(activity["start_date"])
    elapsed = activity.get("elapsed_time", 0)  # seconds
    duration_min = math.ceil(elapsed / 60) if elapsed else None

    activity_type = activity.get("type", "Workout")
    label = ACTIVITY_TYPE_LABELS.get(activity_type, activity_type)
    activity_name = activity.get("name", "").strip()
    # Use the activity's own name; fall back to "<Type> via Strava"
    name = activity_name or f"{label} via Strava"

    distance_m = activity.get("distance")  # metres (float)
    avg_hr = activity.get("average_heartrate")
    calories = activity.get("calories") or activity.get("kilojoules")

    distance_km = round(distance_m / 1000, 3) if distance_m else None

    return {
        "name": name[:120],
        "notes": f"Imported from Strava · {label}",
        "started_at": started_at,
        "ended_at": parse_datetime(activity.get("start_date_local") or activity["start_date"]),
        "duration_min": duration_min,
        "calories_burned": int(calories) if calories else None,
        "distance_km": distance_km,
        "avg_hr_bpm": round(avg_hr) if avg_hr else None,
        "source": "strava",
        "status": "completed",
    }
