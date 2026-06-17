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
def on_achievement_unlocked(sender, instance, created, **kwargs):
    # Unlocks happen in the streak-evaluation pipeline; refresh that too.
    cache.delete(cache_keys.streak(instance.user_id))

    if created:
        try:
            from levels.services import award_xp
            award_xp(
                instance.user, 150,
                f"Unlocked achievement: {instance.achievement.name}",
                "achievement", instance.id,
            )
        except Exception:
            pass
