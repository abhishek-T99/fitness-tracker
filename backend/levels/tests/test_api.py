"""Integration tests for the levels API endpoints."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from levels.models import UserLevel, UserWeeklyChallenge, WeeklyChallenge, XPTransaction
from levels.services import award_xp

User = get_user_model()


def make_user(username, **kw):
    kw.setdefault("email", f"{username}@test.com")
    return User.objects.create_user(username=username, password="pw", **kw)


def auth(client, user):
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


def this_week_start():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


# ── LevelProfileView ──────────────────────────────────────────────────────────

class LevelProfileViewTests(APITestCase):
    url = "/api/v1/levels/profile/"

    def setUp(self):
        self.user = make_user("profile_user")

    def test_auth_required(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creates_profile_on_first_request(self):
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(UserLevel.objects.filter(user=self.user).exists())

    def test_default_profile_values(self):
        auth(self.client, self.user)
        r = self.client.get(self.url)
        data = r.json()
        self.assertEqual(data["level"], 1)
        self.assertEqual(data["tier"], "rookie")
        self.assertEqual(data["total_xp"], 0)
        self.assertEqual(data["prestige_count"], 0)
        self.assertEqual(data["recent_transactions"], [])

    def test_reflects_awarded_xp(self):
        award_xp(self.user, 500, "test", "workout")
        auth(self.client, self.user)
        r = self.client.get(self.url)
        data = r.json()
        self.assertEqual(data["total_xp"], 500)
        self.assertGreater(data["level"], 1)

    def test_xp_progress_fields_present(self):
        auth(self.client, self.user)
        r = self.client.get(self.url)
        data = r.json()
        self.assertIn("xp_in_current_level", data)
        self.assertIn("xp_for_next_level", data)
        self.assertIn("xp_progress_pct", data)

    def test_recent_transactions_capped_at_5(self):
        for i in range(8):
            award_xp(self.user, 10, f"tx {i}", "nutrition")
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertLessEqual(len(r.json()["recent_transactions"]), 5)

    def test_cross_user_isolation(self):
        other = make_user("other_profile")
        award_xp(other, 999, "big", "workout")
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.json()["total_xp"], 0)


# ── XPTransactionListView ─────────────────────────────────────────────────────

class XPTransactionListViewTests(APITestCase):
    url = "/api/v1/levels/transactions/"

    def setUp(self):
        self.user = make_user("tx_user")

    def test_auth_required(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_history(self):
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["count"], 0)
        self.assertEqual(r.json()["results"], [])

    def test_returns_user_transactions(self):
        award_xp(self.user, 50, "a", "workout")
        award_xp(self.user, 30, "b", "nutrition")
        auth(self.client, self.user)
        r = self.client.get(self.url)
        data = r.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)

    def test_default_limit_20(self):
        for i in range(25):
            award_xp(self.user, 10, f"tx{i}", "workout")
        auth(self.client, self.user)
        r = self.client.get(self.url)
        data = r.json()
        self.assertEqual(data["count"], 25)
        self.assertEqual(len(data["results"]), 20)

    def test_custom_limit_and_offset(self):
        for i in range(10):
            award_xp(self.user, 10, f"tx{i}", "workout")
        auth(self.client, self.user)
        r = self.client.get(self.url, {"limit": 3, "offset": 5})
        data = r.json()
        self.assertEqual(data["count"], 10)
        self.assertEqual(len(data["results"]), 3)

    def test_limit_capped_at_100(self):
        for i in range(105):
            award_xp(self.user, 1, f"t{i}", "workout")
        auth(self.client, self.user)
        r = self.client.get(self.url, {"limit": 200})
        self.assertLessEqual(len(r.json()["results"]), 100)

    def test_cross_user_isolation(self):
        other = make_user("other_tx")
        award_xp(other, 100, "theirs", "workout")
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.json()["count"], 0)


# ── ChallengesView ────────────────────────────────────────────────────────────

class ChallengesViewTests(APITestCase):
    url = "/api/v1/levels/challenges/"

    def setUp(self):
        self.user = make_user("challenge_user")
        self.week_start = this_week_start()

    def test_auth_required(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_when_no_challenges_generated(self):
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["challenges"], [])

    def test_returns_challenges_with_user_progress(self):
        ch = WeeklyChallenge.objects.create(
            week_start=self.week_start,
            challenge_type="complete_workouts",
            target_value=5,
            xp_reward=300,
            description="Complete 5 workouts",
        )
        auth(self.client, self.user)
        r = self.client.get(self.url)
        data = r.json()
        self.assertEqual(len(data["challenges"]), 1)
        entry = data["challenges"][0]
        self.assertEqual(entry["current_value"], 0)
        self.assertFalse(entry["completed"])
        self.assertIn("progress_pct", entry)
        self.assertIn("week_start", data)
        self.assertIn("resets_in_secs", data)

    def test_auto_creates_user_challenge_rows(self):
        WeeklyChallenge.objects.create(
            week_start=self.week_start,
            challenge_type="log_meals",
            target_value=7,
            xp_reward=200,
            description="Log meals",
        )
        auth(self.client, self.user)
        self.client.get(self.url)
        self.assertTrue(
            UserWeeklyChallenge.objects.filter(
                user=self.user, challenge__week_start=self.week_start
            ).exists()
        )

    def test_shows_completed_challenge(self):
        ch = WeeklyChallenge.objects.create(
            week_start=self.week_start,
            challenge_type="log_water",
            target_value=1,
            xp_reward=100,
            description="Log water once",
        )
        UserWeeklyChallenge.objects.create(
            user=self.user, challenge=ch,
            current_value=1, completed=True,
            completed_at=timezone.now(),
        )
        auth(self.client, self.user)
        r = self.client.get(self.url)
        entry = r.json()["challenges"][0]
        self.assertTrue(entry["completed"])
        self.assertEqual(entry["progress_pct"], 100.0)

    def test_old_challenges_excluded(self):
        last_week = self.week_start - timedelta(days=7)
        WeeklyChallenge.objects.create(
            week_start=last_week,
            challenge_type="record_pr",
            target_value=1,
            xp_reward=200,
            description="Old PR challenge",
        )
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.json()["challenges"], [])


# ── LeaderboardView ───────────────────────────────────────────────────────────

class LeaderboardViewTests(APITestCase):
    url = "/api/v1/levels/leaderboard/"

    def setUp(self):
        self.user = make_user("leader_user")

    def test_auth_required(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_shows_self_even_with_no_friends(self):
        auth(self.client, self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertTrue(data[0]["is_self"])
        self.assertEqual(data[0]["username"], self.user.username)

    def test_rank_1_has_highest_xp(self):
        from social.models import Friendship
        friend = make_user("big_xp_friend")
        Friendship.objects.create(
            requester=self.user, addressee=friend, status="accepted"
        )
        award_xp(friend, 1000, "lots", "workout")
        auth(self.client, self.user)
        r = self.client.get(self.url)
        data = r.json()
        self.assertEqual(data[0]["rank"], 1)
        self.assertFalse(data[0]["is_self"])
        self.assertEqual(data[0]["username"], "big_xp_friend")

    def test_pending_friendship_excluded(self):
        from social.models import Friendship
        stranger = make_user("pending_friend")
        Friendship.objects.create(
            requester=self.user, addressee=stranger, status="pending"
        )
        auth(self.client, self.user)
        r = self.client.get(self.url)
        ids = [e["user_id"] for e in r.json()]
        self.assertNotIn(stranger.id, ids)

    def test_bidirectional_friendship(self):
        from social.models import Friendship
        friend = make_user("bi_friend")
        # Friendship initiated by the friend
        Friendship.objects.create(
            requester=friend, addressee=self.user, status="accepted"
        )
        auth(self.client, self.user)
        r = self.client.get(self.url)
        ids = [e["user_id"] for e in r.json()]
        self.assertIn(friend.id, ids)

    def test_entry_fields_present(self):
        auth(self.client, self.user)
        r = self.client.get(self.url)
        entry = r.json()[0]
        for field in ("rank", "user_id", "username", "level", "tier", "total_xp", "is_self"):
            self.assertIn(field, entry)


# ── PrestigeView ──────────────────────────────────────────────────────────────

class PrestigeViewTests(APITestCase):
    url = "/api/v1/levels/prestige/"

    def setUp(self):
        self.user = make_user("prestige_user")

    def test_auth_required(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fails_without_level_profile(self):
        auth(self.client, self.user)
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fails_below_level_100(self):
        UserLevel.objects.create(user=self.user, total_xp=500, level=5)
        auth(self.client, self.user)
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("100", r.json()["detail"])

    def test_succeeds_at_level_100(self):
        from levels.services import xp_for_level as xfl
        UserLevel.objects.create(
            user=self.user,
            total_xp=xfl(100),
            level=100,
            tier="immortal",
        )
        auth(self.client, self.user)
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(data["level"], 1)
        self.assertEqual(data["total_xp"], 0)
        self.assertEqual(data["prestige_count"], 1)

    def test_prestige_creates_transaction_record(self):
        from levels.services import xp_for_level as xfl
        UserLevel.objects.create(
            user=self.user,
            total_xp=xfl(100),
            level=100,
            tier="immortal",
        )
        auth(self.client, self.user)
        self.client.post(self.url)
        self.assertTrue(
            XPTransaction.objects.filter(
                user=self.user, source_type="challenge", amount=0
            ).exists()
        )

    def test_fails_at_max_prestige_5(self):
        from levels.services import xp_for_level as xfl
        UserLevel.objects.create(
            user=self.user,
            total_xp=xfl(100),
            level=100,
            tier="immortal",
            prestige_count=5,
        )
        auth(self.client, self.user)
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Maximum", r.json()["detail"])

    def test_prestige_increments_count(self):
        from levels.services import xp_for_level as xfl
        UserLevel.objects.create(
            user=self.user,
            total_xp=xfl(100),
            level=100,
            tier="immortal",
            prestige_count=2,
        )
        auth(self.client, self.user)
        r = self.client.post(self.url)
        self.assertEqual(r.json()["prestige_count"], 3)
