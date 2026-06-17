from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from fitness_tracker import cache_keys

from .models import Meal, MealItem, WaterLog


def _drop_summary(user_id: int, when) -> None:
    """Bust the cached daily summary for the affected user/day."""
    day = when.date() if when else None
    if day:
        cache.delete(cache_keys.nutrition_summary(user_id, day.isoformat()))


@receiver(post_save, sender=Meal)
def on_meal_changed(sender, instance, created, **kwargs):
    _drop_summary(instance.user_id, instance.consumed_at)
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


@receiver([post_save, post_delete], sender=MealItem)
def on_meal_item_changed(sender, instance, **kwargs):
    _drop_summary(instance.meal.user_id, instance.meal.consumed_at)


@receiver(post_save, sender=WaterLog)
def on_water_changed(sender, instance, created, **kwargs):
    _drop_summary(instance.user_id, instance.logged_at)
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
