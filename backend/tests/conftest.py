"""
Shared pytest fixtures.

Hierarchy
---------
api_client          — unauthenticated DRF client
user / other_user   — active User instances (bypass email verification)
auth_client         — DRF client with JWT header for `user`
other_auth_client   — DRF client with JWT header for `other_user`

Domain fixtures (exercise, food, achievement) are provided here because
many test modules need them without caring about specific field values.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import (
    AchievementFactory,
    ExerciseFactory,
    FoodFactory,
    UserFactory,
)


# ---------------------------------------------------------------------------
# HTTP clients
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


def _jwt_client(user):
    """Return an APIClient pre-loaded with a valid JWT for *user*."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def auth_client(user):
    return _jwt_client(user)


@pytest.fixture
def other_auth_client(other_user):
    return _jwt_client(other_user)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    """Primary active user for most tests."""
    return UserFactory()


@pytest.fixture
def other_user(db):
    """Secondary active user for cross-user permission tests."""
    return UserFactory()


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------

@pytest.fixture
def exercise(db):
    return ExerciseFactory()


@pytest.fixture
def food(db):
    return FoodFactory()


@pytest.fixture
def achievement(db):
    return AchievementFactory()
