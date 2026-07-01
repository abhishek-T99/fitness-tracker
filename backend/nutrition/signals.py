from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from fitness_tracker import cache_keys

from .models import Meal, MealItem, WaterLog


def _drop_summary(user_id: int, when) -> None:
    """Bust the cached daily summary for the affected user/day.

    The summary is keyed by the server-local (TIME_ZONE) date, matching
    timezone.localdate() in the read path. `when` comes off the model as
    a UTC-aware datetime, so we must convert to localtime before taking
    .date() — otherwise writes near midnight clear the wrong key and the
    cached summary stays stale until its TTL expires.
    """
    if not when:
        return
    if timezone.is_aware(when):
        when = timezone.localtime(when)
    cache.delete(cache_keys.nutrition_summary(user_id, when.date().isoformat()))


def _bump_nutrition_version(user_id: int) -> None:
    """Invalidate every cached range-summary for this user in one atomic step.

    Range-summary cache keys embed the current version number, so bumping it
    orphans all prior entries without needing delete_pattern or per-key
    tracking. Redis `incr` is atomic; the fallback `set` handles the very
    first write (before the counter exists).
    """
    key = cache_keys.nutrition_version(user_id)
    try:
        cache.incr(key)
    except ValueError:
        # Key doesn't exist yet — seed it. Timeout=None means "no TTL"; if
        # Redis evicts it, incr will fail again and we'll reseed.
        cache.set(key, 2, timeout=None)


@receiver(post_save, sender=Meal)
def on_meal_changed(sender, instance, created, **kwargs):
    _drop_summary(instance.user_id, instance.consumed_at)
    _bump_nutrition_version(instance.user_id)
    if created:
        try:
            from levels.services import award_xp, increment_challenge
            award_xp(instance.user, 10, "Logged a meal", "nutrition", instance.id)
            increment_challenge(instance.user, "log_meals")
        except Exception:
            pass


@receiver(post_delete, sender=Meal)
def on_meal_deleted(sender, instance, **kwargs):
    _drop_summary(instance.user_id, instance.consumed_at)
    _bump_nutrition_version(instance.user_id)


@receiver([post_save, post_delete], sender=MealItem)
def on_meal_item_changed(sender, instance, **kwargs):
    _drop_summary(instance.meal.user_id, instance.meal.consumed_at)
    _bump_nutrition_version(instance.meal.user_id)


@receiver(post_save, sender=WaterLog)
def on_water_changed(sender, instance, created, **kwargs):
    _drop_summary(instance.user_id, instance.logged_at)
    _bump_nutrition_version(instance.user_id)
    if created:
        try:
            from levels.services import award_xp, increment_challenge
            award_xp(instance.user, 5, "Logged water intake", "nutrition", instance.id)
            increment_challenge(instance.user, "log_water")
        except Exception:
            pass


@receiver(post_delete, sender=WaterLog)
def on_water_deleted(sender, instance, **kwargs):
    _drop_summary(instance.user_id, instance.logged_at)
    _bump_nutrition_version(instance.user_id)
