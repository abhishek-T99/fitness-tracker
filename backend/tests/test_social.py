"""
Tests for the social app: friendship lifecycle, post feed isolation,
like toggling, and comments.
"""
import pytest

from tests.factories import FriendshipFactory, PostFactory

FRIENDSHIP_URL = "/api/v1/social/friendships/"
FRIENDS_URL = "/api/v1/social/friendships/friends/"
POST_URL = "/api/v1/social/posts/"
USER_SEARCH_URL = "/api/v1/social/users/"


def friendship_url(pk):
    return f"/api/v1/social/friendships/{pk}/"


def accept_url(pk):
    return f"/api/v1/social/friendships/{pk}/accept/"


def decline_url(pk):
    return f"/api/v1/social/friendships/{pk}/decline/"


def post_url(pk):
    return f"/api/v1/social/posts/{pk}/"


def like_url(pk):
    return f"/api/v1/social/posts/{pk}/like/"


def comment_url(pk):
    return f"/api/v1/social/posts/{pk}/comment/"


# ---------------------------------------------------------------------------
# Friendships
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSendFriendRequest:
    def test_user_can_send_friend_request(self, auth_client, user, other_user):
        res = auth_client.post(FRIENDSHIP_URL, {"addressee": other_user.pk})
        assert res.status_code == 201
        assert res.data["status"] == "pending"

    def test_user_cannot_friend_themselves(self, auth_client, user):
        res = auth_client.post(FRIENDSHIP_URL, {"addressee": user.pk})
        assert res.status_code == 400

    def test_duplicate_request_does_not_create_second_record(self, auth_client, user, other_user):
        auth_client.post(FRIENDSHIP_URL, {"addressee": other_user.pk})
        res = auth_client.post(FRIENDSHIP_URL, {"addressee": other_user.pk})
        # Should return the existing friendship, not create a duplicate.
        assert res.status_code in (200, 201)
        from social.models import Friendship
        assert Friendship.objects.filter(requester=user, addressee=other_user).count() == 1


@pytest.mark.django_db
class TestAcceptFriendRequest:
    def test_addressee_can_accept_pending_request(self, auth_client, other_auth_client, user, other_user):
        # other_user sends request to user
        friendship = FriendshipFactory(requester=other_user, addressee=user, status="pending")
        res = auth_client.post(accept_url(friendship.pk))
        assert res.status_code == 200
        friendship.refresh_from_db()
        assert friendship.status == "accepted"

    def test_requester_cannot_accept_own_request(self, auth_client, user, other_user):
        friendship = FriendshipFactory(requester=user, addressee=other_user, status="pending")
        res = auth_client.post(accept_url(friendship.pk))
        assert res.status_code == 403

    def test_unrelated_user_cannot_accept_request(self, api_client, db):
        from tests.factories import UserFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        third = UserFactory()
        client = APIClient()
        refresh = RefreshToken.for_user(third)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        friendship = FriendshipFactory(status="pending")
        res = client.post(accept_url(friendship.pk))
        assert res.status_code in (403, 404)


@pytest.mark.django_db
class TestDeclineFriendRequest:
    def test_addressee_can_decline_pending_request(self, auth_client, user, other_user):
        friendship = FriendshipFactory(requester=other_user, addressee=user, status="pending")
        res = auth_client.post(decline_url(friendship.pk))
        assert res.status_code == 204

    def test_requester_cannot_decline_own_request(self, auth_client, user, other_user):
        friendship = FriendshipFactory(requester=user, addressee=other_user, status="pending")
        res = auth_client.post(decline_url(friendship.pk))
        assert res.status_code == 403


@pytest.mark.django_db
class TestFriendsList:
    def test_accepted_friends_appear_in_friends_list(self, auth_client, user, other_user):
        FriendshipFactory(requester=user, addressee=other_user, status="accepted")
        res = auth_client.get(FRIENDS_URL)
        assert res.status_code == 200
        assert len(res.data) >= 1

    def test_pending_requests_do_not_appear_in_friends_list(self, auth_client, user, other_user):
        FriendshipFactory(requester=user, addressee=other_user, status="pending")
        res = auth_client.get(FRIENDS_URL)
        assert res.status_code == 200
        assert len(res.data) == 0


# ---------------------------------------------------------------------------
# Posts & feed
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPostFeed:
    def test_feed_includes_own_posts(self, auth_client, user):
        PostFactory(user=user)
        res = auth_client.get(POST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_feed_includes_accepted_friends_posts(self, auth_client, user, other_user):
        FriendshipFactory(requester=user, addressee=other_user, status="accepted")
        PostFactory(user=other_user)
        res = auth_client.get(POST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_feed_excludes_strangers_posts(self, auth_client, other_user):
        PostFactory(user=other_user)
        res = auth_client.get(POST_URL)
        assert res.status_code == 200
        assert res.data["count"] == 0


@pytest.mark.django_db
class TestPostCreate:
    def test_user_can_create_post(self, auth_client, user):
        res = auth_client.post(POST_URL, {"body": "Just crushed leg day!"})
        assert res.status_code == 201
        assert res.data["body"] == "Just crushed leg day!"

    def test_empty_body_returns_400(self, auth_client):
        res = auth_client.post(POST_URL, {"body": ""})
        assert res.status_code == 400


@pytest.mark.django_db
class TestPostDelete:
    def test_owner_can_delete_post(self, auth_client, user):
        post = PostFactory(user=user)
        res = auth_client.delete(post_url(post.pk))
        assert res.status_code == 204

    def test_non_owner_cannot_delete_post(self, auth_client, other_user):
        post = PostFactory(user=other_user)
        res = auth_client.delete(post_url(post.pk))
        assert res.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Likes
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPostLike:
    def test_first_like_creates_a_like(self, auth_client, user):
        # Like own post — always in the feed regardless of friendship.
        post = PostFactory(user=user)
        res = auth_client.post(like_url(post.pk))
        assert res.status_code == 200
        assert res.data["liked"] is True
        assert res.data["likes_count"] == 1

    def test_second_like_toggles_it_off(self, auth_client, user):
        post = PostFactory(user=user)
        auth_client.post(like_url(post.pk))  # like
        res = auth_client.post(like_url(post.pk))  # unlike
        assert res.status_code == 200
        assert res.data["liked"] is False
        assert res.data["likes_count"] == 0


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPostComment:
    def test_user_can_comment_on_accessible_post(self, auth_client, user, other_user):
        FriendshipFactory(requester=user, addressee=other_user, status="accepted")
        post = PostFactory(user=other_user)
        res = auth_client.post(comment_url(post.pk), {"body": "Great work!"})
        assert res.status_code == 201
        assert res.data["body"] == "Great work!"

    def test_empty_comment_body_returns_400(self, auth_client, user):
        post = PostFactory(user=user)
        res = auth_client.post(comment_url(post.pk), {"body": ""})
        assert res.status_code == 400
