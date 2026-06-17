"""Signal hooks for goals — award XP when a goal is achieved."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Goal


@receiver(post_save, sender=Goal)
def on_goal_saved(sender, instance, created, **kwargs):
    if instance.status != Goal.Status.ACHIEVED:
        return
    # Only award on the transition to ACHIEVED, not on every subsequent save.
    # We guard with an XPTransaction existence check inside award_xp itself.
    try:
        from levels.services import award_xp
        award_xp(instance.user, 150, f"Achieved goal: {instance.title}", "goal", instance.id)
    except Exception:
        pass
