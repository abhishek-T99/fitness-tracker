from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from fitness_tracker import cache_keys

from .models import Meal, MealItem, WaterLog


def _drop_summary(user_id: int, when) -> None:
    """Bust the cached daily summary for the affected user/day.

    `when` may be a datetime (Meal.consumed_at / WaterLog.logged_at) or None;
    if missing, we drop today's key as the safe default.
    """
    day = when.date() if when else None
    if day:
        cache.delete(cache_keys.nutrition_summary(user_id, day.isoformat()))


@receiver([post_save, post_delete], sender=Meal)
def on_meal_changed(sender, instance, **kwargs):
    _drop_summary(instance.user_id, instance.consumed_at)


@receiver([post_save, post_delete], sender=MealItem)
def on_meal_item_changed(sender, instance, **kwargs):
    _drop_summary(instance.meal.user_id, instance.meal.consumed_at)


@receiver([post_save, post_delete], sender=WaterLog)
def on_water_changed(sender, instance, **kwargs):
    _drop_summary(instance.user_id, instance.logged_at)
