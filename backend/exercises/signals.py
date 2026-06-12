from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Exercise
from .views import LIST_CACHE_PREFIX


@receiver([post_save, post_delete], sender=Exercise)
def invalidate_exercise_cache(sender, **kwargs):
    """Blow away every cached variant of the list endpoint.

    Exercise mutations are rare (admin-only seed updates), so a broad
    pattern-delete is fine — we'd rather lose a couple hundred bytes of
    cache than serve stale catalog data.
    """
    cache.delete_pattern(f"{LIST_CACHE_PREFIX}*")
