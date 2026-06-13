"""
Signal handlers that create Notification records in response to social events.

Rules enforced here:
  - No self-notifications (actor == recipient is always skipped).
  - Friendship accepted: idempotent via get_or_create so repeated saves
    on an already-accepted friendship never duplicate the notification.
  - Only created=True triggers for Like / Comment / UserAchievement
    (updates never produce a notification for those models).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


def _display_name(user) -> str:
    return user.get_full_name().strip() or user.username


@receiver(post_save, sender="social.Like")
def on_like_created(sender, instance, created, **kwargs):
    if not created:
        return
    post = instance.post
    if instance.user_id == post.user_id:
        return  # no self-notification
    from .models import Notification
    Notification.objects.create(
        recipient=post.user,
        actor=instance.user,
        notif_type=Notification.Type.LIKE,
        message=f"{_display_name(instance.user)} liked your post.",
        target_url="/social",
    )


@receiver(post_save, sender="social.Comment")
def on_comment_created(sender, instance, created, **kwargs):
    if not created:
        return
    post = instance.post
    if instance.user_id == post.user_id:
        return
    from .models import Notification
    Notification.objects.create(
        recipient=post.user,
        actor=instance.user,
        notif_type=Notification.Type.COMMENT,
        message=f"{_display_name(instance.user)} commented on your post.",
        target_url="/social",
    )


@receiver(post_save, sender="social.Friendship")
def on_friendship_changed(sender, instance, created, **kwargs):
    from .models import Notification

    if created and instance.status == "pending":
        Notification.objects.create(
            recipient=instance.addressee,
            actor=instance.requester,
            notif_type=Notification.Type.FRIEND_REQUEST,
            message=f"{_display_name(instance.requester)} sent you a friend request.",
            target_url="/social",
        )
    elif not created and instance.status == "accepted":
        # get_or_create prevents duplicates when an accepted friendship
        # is saved more than once (e.g. unrelated field update).
        Notification.objects.get_or_create(
            recipient=instance.requester,
            actor=instance.addressee,
            notif_type=Notification.Type.FRIEND_ACCEPTED,
            defaults={
                "message": f"{_display_name(instance.addressee)} accepted your friend request.",
                "target_url": "/social",
            },
        )


@receiver(post_save, sender="achievements.UserAchievement")
def on_achievement_unlocked(sender, instance, created, **kwargs):
    if not created:
        return
    from .models import Notification
    Notification.objects.create(
        recipient=instance.user,
        actor=None,
        notif_type=Notification.Type.ACHIEVEMENT,
        message=f"Achievement unlocked: {instance.achievement.name}",
        target_url="/achievements",
    )
