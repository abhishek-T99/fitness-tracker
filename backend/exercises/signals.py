from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from fitness_tracker import cache_keys

from .models import Exercise


@receiver([post_save, post_delete], sender=Exercise)
def invalidate_exercise_cache(sender, **kwargs):
    """Blow away every cached variant of the list endpoint.

    Exercise mutations are rare (admin-only seed updates), so a broad
    pattern-delete is fine — we'd rather lose a couple hundred bytes of
    cache than serve stale catalog data.
    """
    cache.delete_pattern(f"{cache_keys.EXERCISE_LIST_VARIANT_PREFIX}*")
