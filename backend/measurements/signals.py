"""Signal hooks for measurements — invalidate progress body-composition cache + XP."""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import BodyMeasurement


@receiver(post_save, sender=BodyMeasurement)
def on_measurement_saved(sender, instance, created, **kwargs):
    try:
        cache.delete_pattern(f"progress:body_comp:{instance.user_id}:*")
    except AttributeError:
        pass  # non-redis backend in tests

    if created:
        try:
            from levels.services import award_xp, increment_challenge
            award_xp(instance.user, 25, "Logged a measurement", "measurement", instance.id)
            increment_challenge(instance.user, "log_measurement")
        except Exception:
            pass


@receiver(post_delete, sender=BodyMeasurement)
def on_measurement_deleted(sender, instance, **kwargs):
    try:
        cache.delete_pattern(f"progress:body_comp:{instance.user_id}:*")
    except AttributeError:
        pass
