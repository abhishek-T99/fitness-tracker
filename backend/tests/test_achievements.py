"""Tests for the achievements app: catalog, unlocked badges, and streak."""
import pytest

from tests.factories import (
    AchievementFactory,
    StreakFactory,
    UserAchievementFactory,
    WorkoutFactory,
)

CATALOG_URL = "/api/v1/achievements/catalog/"
UNLOCKED_URL = "/api/v1/achievements/unlocked/"
STREAK_URL = "/api/v1/achievements/streak/"


def catalog_url(pk):
    return f"/api/v1/achievements/catalog/{pk}/"


@pytest.mark.django_db
class TestAchievementCatalog:
    def test_lists_all_achievements(self, auth_client):
        AchievementFactory.create_batch(3)
        res = auth_client.get(CATALOG_URL)
        assert res.status_code == 200
        assert len(res.data) == 3

    def test_detail_returns_achievement(self, auth_client, achievement):
        res = auth_client.get(catalog_url(achievement.pk))
        assert res.status_code == 200
        assert res.data["code"] == achievement.code

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(CATALOG_URL)
        assert res.status_code == 401


@pytest.mark.django_db
class TestUnlockedAchievements:
    def test_returns_only_current_users_unlocked_achievements(self, auth_client, user, other_user, achievement):
        UserAchievementFactory(user=user, achievement=achievement)
        UserAchievementFactory(user=other_user, achievement=AchievementFactory())
        res = auth_client.get(UNLOCKED_URL)
        assert res.status_code == 200
        assert len(res.data) == 1

    def test_empty_when_no_achievements_unlocked(self, auth_client):
        res = auth_client.get(UNLOCKED_URL)
        assert res.status_code == 200
        assert len(res.data) == 0


@pytest.mark.django_db
class TestStreak:
    def test_returns_streak_data_structure(self, auth_client, user):
        res = auth_client.get(STREAK_URL)
        assert res.status_code == 200
        assert "current_days" in res.data
        assert "longest_days" in res.data

    def test_new_user_starts_with_zero_streak(self, auth_client, user):
        res = auth_client.get(STREAK_URL)
        assert res.data["current_days"] == 0

    def test_streak_reflects_existing_record(self, auth_client, user):
        StreakFactory(user=user, current_days=7, longest_days=14)
        res = auth_client.get(STREAK_URL)
        assert res.data["current_days"] == 7
        assert res.data["longest_days"] == 14

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(STREAK_URL)
        assert res.status_code == 401
