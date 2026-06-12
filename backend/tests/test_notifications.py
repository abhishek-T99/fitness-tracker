"""
Tests for the notifications app.

Covers:
  - API: list (own only, unread-first ordering), unread_count, mark single read,
    cannot mark another user's notification, mark_all_read
  - Signals: like, comment, friend_request, friend_accepted, achievement unlock
  - No self-notification (liking/commenting your own post)
  - Idempotency: duplicate accepted-friendship save does not double-notify
"""
import pytest

from tests.factories import (
    CommentFactory,
    FriendshipFactory,
    LikeFactory,
    NotificationFactory,
    PostFactory,
    UserAchievementFactory,
)

NOTIFICATIONS_URL = "/api/v1/notifications/"
UNREAD_COUNT_URL  = "/api/v1/notifications/unread_count/"
MARK_ALL_READ_URL = "/api/v1/notifications/mark_all_read/"


def notification_url(pk):
    return f"/api/v1/notifications/{pk}/"


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationList:
    def test_returns_only_own_notifications(self, auth_client, user, other_user):
        NotificationFactory(recipient=user)
        NotificationFactory(recipient=other_user)
        res = auth_client.get(NOTIFICATIONS_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(NOTIFICATIONS_URL)
        assert res.status_code == 401

    def test_unread_appear_before_read(self, auth_client, user):
        NotificationFactory(recipient=user, read=True)
        unread = NotificationFactory(recipient=user, read=False)
        res = auth_client.get(NOTIFICATIONS_URL)
        assert res.status_code == 200
        assert res.data["results"][0]["id"] == unread.id


# ---------------------------------------------------------------------------
# Unread count
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUnreadCount:
    def test_returns_correct_unread_count(self, auth_client, user):
        NotificationFactory.create_batch(3, recipient=user, read=False)
        NotificationFactory(recipient=user, read=True)
        res = auth_client.get(UNREAD_COUNT_URL)
        assert res.status_code == 200
        assert res.data["count"] == 3

    def test_returns_zero_when_no_notifications(self, auth_client):
        res = auth_client.get(UNREAD_COUNT_URL)
        assert res.status_code == 200
        assert res.data["count"] == 0


# ---------------------------------------------------------------------------
# Mark read
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMarkRead:
    def test_mark_single_notification_as_read(self, auth_client, user):
        notif = NotificationFactory(recipient=user, read=False)
        res = auth_client.patch(notification_url(notif.pk), {"read": True})
        assert res.status_code == 200
        notif.refresh_from_db()
        assert notif.read is True

    def test_cannot_mark_another_users_notification(self, auth_client, other_user):
        notif = NotificationFactory(recipient=other_user, read=False)
        res = auth_client.patch(notification_url(notif.pk), {"read": True})
        assert res.status_code == 404

    def test_mark_all_read_clears_unread(self, auth_client, user):
        NotificationFactory.create_batch(4, recipient=user, read=False)
        res = auth_client.post(MARK_ALL_READ_URL)
        assert res.status_code == 204
        from notifications.models import Notification
        assert Notification.objects.filter(recipient=user, read=False).count() == 0

    def test_mark_all_read_does_not_affect_other_users(self, auth_client, user, other_user):
        NotificationFactory.create_batch(2, recipient=other_user, read=False)
        auth_client.post(MARK_ALL_READ_URL)
        from notifications.models import Notification
        assert Notification.objects.filter(recipient=other_user, read=False).count() == 2


# ---------------------------------------------------------------------------
# Signal: Like
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLikeSignal:
    def test_like_creates_notification_for_post_owner(self, user, other_user):
        post = PostFactory(user=user)
        LikeFactory(post=post, user=other_user)
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="like"
        ).count() == 1

    def test_like_notification_references_actor(self, user, other_user):
        post = PostFactory(user=user)
        LikeFactory(post=post, user=other_user)
        from notifications.models import Notification
        notif = Notification.objects.get(recipient=user, notif_type="like")
        assert notif.actor == other_user

    def test_liking_own_post_does_not_notify_self(self, user):
        post = PostFactory(user=user)
        LikeFactory(post=post, user=user)
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="like"
        ).count() == 0


# ---------------------------------------------------------------------------
# Signal: Comment
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCommentSignal:
    def test_comment_creates_notification_for_post_owner(self, user, other_user):
        post = PostFactory(user=user)
        CommentFactory(post=post, user=other_user)
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="comment"
        ).count() == 1

    def test_comment_notification_references_actor(self, user, other_user):
        post = PostFactory(user=user)
        CommentFactory(post=post, user=other_user)
        from notifications.models import Notification
        notif = Notification.objects.get(recipient=user, notif_type="comment")
        assert notif.actor == other_user

    def test_commenting_on_own_post_does_not_notify_self(self, user):
        post = PostFactory(user=user)
        CommentFactory(post=post, user=user)
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="comment"
        ).count() == 0


# ---------------------------------------------------------------------------
# Signal: Friendship
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFriendshipSignal:
    def test_friend_request_notifies_addressee(self, user, other_user):
        FriendshipFactory(requester=other_user, addressee=user, status="pending")
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="friend_request"
        ).count() == 1

    def test_friend_accepted_notifies_requester(self, user, other_user):
        friendship = FriendshipFactory(requester=user, addressee=other_user, status="pending")
        friendship.status = "accepted"
        friendship.save()
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="friend_accepted"
        ).count() == 1

    def test_no_duplicate_accepted_notification_on_repeated_save(self, user, other_user):
        friendship = FriendshipFactory(requester=user, addressee=other_user, status="pending")
        friendship.status = "accepted"
        friendship.save()
        friendship.save()  # second save must not create a second notification
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="friend_accepted"
        ).count() == 1

    def test_creating_accepted_friendship_directly_does_not_notify(self, user, other_user):
        # Seeding creates accepted friendships directly — no notification expected
        FriendshipFactory(requester=user, addressee=other_user, status="accepted")
        from notifications.models import Notification
        assert Notification.objects.filter(notif_type="friend_accepted").count() == 0


# ---------------------------------------------------------------------------
# Signal: Achievement
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAchievementSignal:
    def test_achievement_unlock_creates_notification(self, user):
        UserAchievementFactory(user=user)
        from notifications.models import Notification
        assert Notification.objects.filter(
            recipient=user, notif_type="achievement"
        ).count() == 1

    def test_achievement_notification_has_correct_url(self, user):
        UserAchievementFactory(user=user)
        from notifications.models import Notification
        notif = Notification.objects.get(recipient=user, notif_type="achievement")
        assert notif.target_url == "/achievements"
