"""
Tests for social authentication (Google + Facebook).

Strategy
--------
We never call Google/Facebook in tests. Two layers, two mock boundaries:

1. Verifier unit tests  — mock the *network* (google lib / requests.get) and
   assert our normalization + rejection logic.
2. View tests           — mock the *verifier* and assert our side of the
   contract: user provisioning, account linking by email, activation,
   username uniqueness, JWT issuance, error mapping.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from accounts.social import SocialAuthError, verify_facebook_token, verify_google_token
from tests.factories import UserFactory

User = get_user_model()

GOOGLE_URL = "/api/v1/auth/google/"
FACEBOOK_URL = "/api/v1/auth/facebook/"

SOCIAL_INFO = {
    "email": "jane@gmail.com",
    "first_name": "Jane",
    "last_name": "Doe",
}


# ---------------------------------------------------------------------------
# Verifier: Google
# ---------------------------------------------------------------------------

class TestGoogleVerifier:
    @patch("accounts.social.google_id_token.verify_oauth2_token")
    def test_valid_token_returns_normalized_info(self, mock_verify):
        mock_verify.return_value = {
            "email": "jane@gmail.com",
            "email_verified": True,
            "given_name": "Jane",
            "family_name": "Doe",
        }
        info = verify_google_token("fake-id-token")
        assert info == SOCIAL_INFO

    @patch("accounts.social.google_id_token.verify_oauth2_token")
    def test_unverified_email_is_rejected(self, mock_verify):
        mock_verify.return_value = {
            "email": "jane@gmail.com",
            "email_verified": False,
        }
        with pytest.raises(SocialAuthError):
            verify_google_token("fake-id-token")

    @patch("accounts.social.google_id_token.verify_oauth2_token")
    def test_invalid_token_raises(self, mock_verify):
        mock_verify.side_effect = ValueError("Token expired")
        with pytest.raises(SocialAuthError):
            verify_google_token("bad-token")


# ---------------------------------------------------------------------------
# Verifier: Facebook
# ---------------------------------------------------------------------------

def _fb_response(payload, ok=True):
    class R:
        status_code = 200 if ok else 400

        def json(self):
            return payload

    return R()


class TestFacebookVerifier:
    @patch("accounts.social.requests.get")
    def test_valid_token_returns_normalized_info(self, mock_get):
        mock_get.side_effect = [
            _fb_response({"data": {"is_valid": True, "app_id": "test-app-id"}}),
            _fb_response({
                "id": "123",
                "email": "jane@gmail.com",
                "first_name": "Jane",
                "last_name": "Doe",
            }),
        ]
        info = verify_facebook_token("fake-access-token")
        assert info == SOCIAL_INFO

    @patch("accounts.social.requests.get")
    def test_invalid_token_is_rejected(self, mock_get):
        mock_get.return_value = _fb_response({"data": {"is_valid": False}})
        with pytest.raises(SocialAuthError):
            verify_facebook_token("bad-token")

    @patch("accounts.social.requests.get")
    def test_token_for_wrong_app_is_rejected(self, mock_get):
        mock_get.return_value = _fb_response(
            {"data": {"is_valid": True, "app_id": "someone-elses-app"}}
        )
        with pytest.raises(SocialAuthError):
            verify_facebook_token("stolen-token")

    @patch("accounts.social.requests.get")
    def test_missing_email_is_rejected(self, mock_get):
        # User can deny the email permission — we can't link an account then.
        mock_get.side_effect = [
            _fb_response({"data": {"is_valid": True, "app_id": "test-app-id"}}),
            _fb_response({"id": "123", "first_name": "Jane", "last_name": "Doe"}),
        ]
        with pytest.raises(SocialAuthError):
            verify_facebook_token("fake-access-token")


# ---------------------------------------------------------------------------
# View: Google login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGoogleLoginView:
    @patch("accounts.views.verify_google_token", return_value=dict(SOCIAL_INFO))
    def test_new_user_is_created_and_gets_tokens(self, _, api_client):
        res = api_client.post(GOOGLE_URL, {"token": "fake"})
        assert res.status_code == 200
        assert "access" in res.data["tokens"]
        assert "refresh" in res.data["tokens"]
        user = User.objects.get(email="jane@gmail.com")
        assert user.is_active is True
        assert user.first_name == "Jane"
        assert not user.has_usable_password()

    @patch("accounts.views.verify_google_token", return_value=dict(SOCIAL_INFO))
    def test_existing_user_is_linked_not_duplicated(self, _, api_client):
        existing = UserFactory(email="jane@gmail.com")
        res = api_client.post(GOOGLE_URL, {"token": "fake"})
        assert res.status_code == 200
        assert User.objects.filter(email__iexact="jane@gmail.com").count() == 1
        assert res.data["user"]["id"] == existing.id

    @patch("accounts.views.verify_google_token", return_value=dict(SOCIAL_INFO))
    def test_email_match_is_case_insensitive(self, _, api_client):
        UserFactory(email="Jane@Gmail.com")
        api_client.post(GOOGLE_URL, {"token": "fake"})
        assert User.objects.count() == 1

    @patch("accounts.views.verify_google_token", return_value=dict(SOCIAL_INFO))
    def test_inactive_user_is_activated(self, _, api_client):
        # Registered via email but never verified — provider has now verified
        # the same address, so the account is activated.
        existing = UserFactory(email="jane@gmail.com", is_active=False)
        res = api_client.post(GOOGLE_URL, {"token": "fake"})
        assert res.status_code == 200
        existing.refresh_from_db()
        assert existing.is_active is True

    @patch("accounts.views.verify_google_token", return_value=dict(SOCIAL_INFO))
    def test_username_collision_gets_unique_suffix(self, _, api_client):
        UserFactory(username="jane")  # occupies the email local-part
        res = api_client.post(GOOGLE_URL, {"token": "fake"})
        assert res.status_code == 200
        created = User.objects.get(email="jane@gmail.com")
        assert created.username != "jane"
        assert created.username.startswith("jane")

    @patch(
        "accounts.views.verify_google_token",
        side_effect=SocialAuthError("Invalid token."),
    )
    def test_invalid_token_returns_401(self, _, api_client):
        res = api_client.post(GOOGLE_URL, {"token": "bad"})
        assert res.status_code == 401
        assert User.objects.count() == 0

    def test_missing_token_returns_400(self, api_client):
        res = api_client.post(GOOGLE_URL, {})
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# View: Facebook login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacebookLoginView:
    @patch("accounts.views.verify_facebook_token", return_value=dict(SOCIAL_INFO))
    def test_new_user_is_created_and_gets_tokens(self, _, api_client):
        res = api_client.post(FACEBOOK_URL, {"token": "fake"})
        assert res.status_code == 200
        assert "access" in res.data["tokens"]
        assert User.objects.filter(email="jane@gmail.com").exists()

    @patch(
        "accounts.views.verify_facebook_token",
        side_effect=SocialAuthError("Invalid token."),
    )
    def test_invalid_token_returns_401(self, _, api_client):
        res = api_client.post(FACEBOOK_URL, {"token": "bad"})
        assert res.status_code == 401

    def test_missing_token_returns_400(self, api_client):
        res = api_client.post(FACEBOOK_URL, {})
        assert res.status_code == 400
