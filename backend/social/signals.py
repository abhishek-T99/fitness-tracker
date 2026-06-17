"""Signal hooks for social — award XP for community engagement."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post


@receiver(post_save, sender=Post)
def on_post_created(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from levels.services import award_xp
        award_xp(instance.user, 15, "Shared a post", "social", instance.id)
    except Exception:
        pass
