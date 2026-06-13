"""Celery tasks for integration data sync."""
import logging
from datetime import datetime, timedelta, timezone as dt_timezone

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def sync_intervals_activities(self, integration_id: int, days_back: int = 7):
    """
    Pull recent activities from Intervals.icu and create/update Workouts.

    Called by the Celery beat schedule (periodic) and manually on first connect
    (with days_back=30 to backfill).
    """
    from .models import Integration, SyncLog
    from .intervals import IntervalsError, get_activities, map_activity_to_workout
    from workouts.models import Workout

    try:
        integration = Integration.objects.select_related("token").get(pk=integration_id)
    except Integration.DoesNotExist:
        logger.error("sync_intervals_activities: integration %s not found", integration_id)
        return

    token = integration.token
    athlete_id = token.athlete_id
    api_key = token.access_token  # API key stored in access_token field

    oldest = (timezone.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        activities = get_activities(athlete_id, api_key, oldest=oldest)
    except IntervalsError as exc:
        SyncLog.objects.create(
            integration=integration,
            event_type="activity.sync",
            status=SyncLog.Status.FAILED,
            detail=str(exc),
        )
        raise self.retry(exc=exc)

    created = updated = skipped = 0

    for activity in activities:
        external_id = str(activity.get("id", ""))
        if not external_id:
            continue

        # Check for existing sync log (dedup)
        existing_log = (
            SyncLog.objects
            .filter(
                integration=integration,
                external_id=external_id,
                status=SyncLog.Status.SUCCESS,
                event_type="activity.create",
            )
            .select_related("workout")
            .first()
        )

        workout_kwargs = map_activity_to_workout(activity)

        if existing_log and existing_log.workout:
            # Update if the name or duration changed
            w = existing_log.workout
            changed = any(
                getattr(w, k) != v
                for k, v in workout_kwargs.items()
                if k in ("name", "duration_min", "calories_burned")
            )
            if changed:
                for field, value in workout_kwargs.items():
                    setattr(w, field, value)
                w.save()
                SyncLog.objects.create(
                    integration=integration,
                    event_type="activity.update",
                    external_id=external_id,
                    status=SyncLog.Status.SUCCESS,
                    detail="Workout updated from Intervals.icu.",
                    workout=w,
                )
                updated += 1
            else:
                skipped += 1
            continue

        workout = Workout.objects.create(user=integration.user, **workout_kwargs)
        SyncLog.objects.create(
            integration=integration,
            event_type="activity.create",
            external_id=external_id,
            status=SyncLog.Status.SUCCESS,
            detail=f"Workout created from Intervals.icu activity {external_id}.",
            workout=workout,
        )
        created += 1

    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at"])

    logger.info(
        "Intervals.icu sync [integration=%s]: created=%s updated=%s skipped=%s",
        integration_id, created, updated, skipped,
    )
    return {"created": created, "updated": updated, "skipped": skipped}


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def sync_intervals_wellness(self, integration_id: int, days_back: int = 7):
    """
    Pull daily wellness data from Intervals.icu and upsert into BodyMeasurement.

    Wellness fields mapped:
      restingHR  → resting_hr_bpm
      weight     → weight_kg  (Intervals stores in kg)
      steps      → stored in notes (no dedicated column)
      hrv        → stored in notes
      sleepScore → stored in notes
    """
    from datetime import date as date_type
    from .models import Integration, SyncLog
    from .intervals import IntervalsError, get_wellness
    from measurements.models import BodyMeasurement

    try:
        integration = Integration.objects.select_related("token").get(pk=integration_id)
    except Integration.DoesNotExist:
        return

    token = integration.token
    oldest = (timezone.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        entries = get_wellness(token.athlete_id, token.access_token, oldest=oldest)
    except IntervalsError as exc:
        SyncLog.objects.create(
            integration=integration,
            event_type="wellness.sync",
            status=SyncLog.Status.FAILED,
            detail=str(exc),
        )
        raise self.retry(exc=exc)

    upserted = 0
    for entry in entries:
        # id field is the date string "YYYY-MM-DD"
        date_str = entry.get("id") or entry.get("date")
        if not date_str:
            continue

        try:
            recorded_at = date_type.fromisoformat(date_str)
        except ValueError:
            continue

        resting_hr = entry.get("restingHR")
        weight = entry.get("weight")      # kg
        steps = entry.get("steps")
        hrv = entry.get("hrv")
        sleep_score = entry.get("sleepScore")

        # Only upsert if there's at least one meaningful value
        if not any([resting_hr, weight, steps, hrv, sleep_score]):
            continue

        defaults = {"notes": "Synced from Intervals.icu"}
        if resting_hr:
            defaults["resting_hr_bpm"] = int(resting_hr)
        if weight:
            defaults["weight_kg"] = round(float(weight), 2)
        if steps is not None:
            defaults["steps"] = int(steps)
        if hrv is not None:
            defaults["hrv_rmssd"] = round(float(hrv), 2)
        if sleep_score is not None:
            defaults["sleep_score"] = int(sleep_score)

        # Always upsert when steps > 0 or any body metric is present.
        # Skip if the entry would only contain an empty shell with notes only.
        has_body_data = any([
            defaults.get("resting_hr_bpm"),
            defaults.get("weight_kg"),
            defaults.get("steps"),
            defaults.get("hrv_rmssd"),
            defaults.get("sleep_score"),
        ])
        if not has_body_data:
            continue

        BodyMeasurement.objects.update_or_create(
            user=integration.user,
            recorded_at=recorded_at,
            defaults=defaults,
        )
        upserted += 1

    logger.info(
        "Intervals.icu wellness sync [integration=%s]: upserted=%s entries",
        integration_id, upserted,
    )
    return {"upserted": upserted}


@shared_task
def sync_all_intervals_integrations():
    """Fan-out: schedule activity + wellness sync for every active Intervals.icu integration."""
    from .models import Integration, Provider

    ids = list(Integration.objects.filter(
        provider=Provider.INTERVALS, is_active=True
    ).values_list("pk", flat=True))

    for pk in ids:
        sync_intervals_activities.delay(pk, days_back=1)
        sync_intervals_wellness.delay(pk, days_back=1)

    logger.info("sync_all_intervals_integrations: queued %d integrations", len(ids))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_strava_activity(self, integration_id: int, activity_id: int, event_type: str):
    """
    Fetch a Strava activity and create/update/delete the corresponding Workout.

    Called from the webhook view for create/update events, and directly for
    manual re-syncs.
    """
    from .models import Integration, SyncLog
    from .strava import StravaError, ensure_fresh_token, get_activity, map_activity_to_workout
    from workouts.models import Workout

    try:
        integration = Integration.objects.select_related("token").get(pk=integration_id)
    except Integration.DoesNotExist:
        logger.error("process_strava_activity: integration %s not found", integration_id)
        return

    external_id = str(activity_id)

    if event_type == "activity.delete":
        # Remove the workout that was created for this Strava activity
        log = (
            SyncLog.objects
            .filter(integration=integration, external_id=external_id, workout__isnull=False)
            .select_related("workout")
            .first()
        )
        if log and log.workout:
            log.workout.delete()
            SyncLog.objects.create(
                integration=integration,
                event_type=event_type,
                external_id=external_id,
                status=SyncLog.Status.SUCCESS,
                detail="Workout deleted.",
            )
        return

    try:
        access_token = ensure_fresh_token(integration.token)
        activity = get_activity(access_token, activity_id)
    except StravaError as exc:
        SyncLog.objects.create(
            integration=integration,
            event_type=event_type,
            external_id=external_id,
            status=SyncLog.Status.FAILED,
            detail=str(exc),
        )
        raise self.retry(exc=exc)

    # Skip activities that belong to a different athlete (safety check)
    athlete_id = str(activity.get("athlete", {}).get("id", ""))
    if integration.token.athlete_id and athlete_id != integration.token.athlete_id:
        SyncLog.objects.create(
            integration=integration,
            event_type=event_type,
            external_id=external_id,
            status=SyncLog.Status.SKIPPED,
            detail="Athlete ID mismatch.",
        )
        return

    workout_kwargs = map_activity_to_workout(activity)

    if event_type == "activity.update":
        # Update the existing workout if we have one
        log = (
            SyncLog.objects
            .filter(integration=integration, external_id=external_id, workout__isnull=False)
            .select_related("workout")
            .first()
        )
        if log and log.workout:
            for field, value in workout_kwargs.items():
                setattr(log.workout, field, value)
            log.workout.save()
            SyncLog.objects.create(
                integration=integration,
                event_type=event_type,
                external_id=external_id,
                status=SyncLog.Status.SUCCESS,
                detail="Workout updated.",
                workout=log.workout,
            )
            integration.last_synced_at = timezone.now()
            integration.save(update_fields=["last_synced_at"])
            return

    # activity.create (or update without an existing workout)
    # Guard against duplicates
    if SyncLog.objects.filter(
        integration=integration,
        external_id=external_id,
        status=SyncLog.Status.SUCCESS,
        event_type="activity.create",
    ).exists():
        SyncLog.objects.create(
            integration=integration,
            event_type=event_type,
            external_id=external_id,
            status=SyncLog.Status.SKIPPED,
            detail="Already synced.",
        )
        return

    workout = Workout.objects.create(user=integration.user, **workout_kwargs)
    SyncLog.objects.create(
        integration=integration,
        event_type="activity.create",
        external_id=external_id,
        status=SyncLog.Status.SUCCESS,
        detail=f"Workout created from Strava activity {activity_id}.",
        workout=workout,
    )
    integration.last_synced_at = timezone.now()
    integration.save(update_fields=["last_synced_at"])
