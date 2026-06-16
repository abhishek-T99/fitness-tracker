"""Signal hooks for measurements — invalidate progress body-composition cache."""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import BodyMeasurement


@receiver([post_save, post_delete], sender=BodyMeasurement)
def on_measurement_changed(sender, instance, **kwargs):
    try:
        cache.delete_pattern(f"progress:body_comp:{instance.user_id}:*")
    except AttributeError:
        pass  # non-redis backend in tests
