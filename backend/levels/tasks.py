from celery import shared_task


@shared_task(name="levels.tasks.generate_weekly_challenges")
def generate_weekly_challenges_task():
    """
    Runs every Monday at 00:05 UTC.
    Generates 3 fresh WeeklyChallenge objects for the new week.
    """
    from datetime import timedelta
    from django.utils import timezone
    from .services import generate_weekly_challenges

    today      = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())  # Monday
    created    = generate_weekly_challenges(week_start)
    return f"Generated {len(created)} challenges for week starting {week_start}"


@shared_task(name="levels.tasks.update_athlete_classes")
def update_athlete_classes_task():
    """
    Runs every Monday at 03:00 UTC.
    Recalculates the athlete class for every user who has a level profile.
    """
    from django.contrib.auth import get_user_model
    from .models import UserLevel
    from .services import detect_athlete_class

    User = get_user_model()
    updated = 0
    for ul in UserLevel.objects.select_related("user").iterator(chunk_size=100):
        new_class = detect_athlete_class(ul.user)
        if new_class != ul.athlete_class:
            ul.athlete_class = new_class
            ul.save(update_fields=["athlete_class", "updated_at"])
            updated += 1

    return f"Updated athlete class for {updated} users"
