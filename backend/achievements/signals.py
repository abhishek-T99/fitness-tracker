from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from fitness_tracker import cache_keys

from .models import Achievement, Streak, UserAchievement


@receiver([post_save, post_delete], sender=Achievement)
def invalidate_catalog(sender, **kwargs):
    cache.delete(cache_keys.ACHIEVEMENT_CATALOG)


@receiver(post_save, sender=Streak)
def invalidate_streak(sender, instance, **kwargs):
    cache.delete(cache_keys.streak(instance.user_id))


@receiver(post_save, sender=UserAchievement)
def invalidate_streak_on_unlock(sender, instance, **kwargs):
    # Unlocks happen in the streak-evaluation pipeline; refresh that too.
    cache.delete(cache_keys.streak(instance.user_id))
