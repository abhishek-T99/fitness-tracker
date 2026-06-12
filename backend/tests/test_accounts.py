"""
Tests for the accounts app: registration, email verification, login,
profile management, and password flows.
"""
import pytest
from django.core import mail, signing
from django.contrib.auth import get_user_model

from tests.factories import UserFactory
from accounts.tokens import make_email_verify_token, make_password_reset_token

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"
VERIFY_URL = "/api/v1/auth/verify-email/"
RESEND_URL = "/api/v1/auth/resend-verification/"
LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"
ME_URL = "/api/v1/auth/me/"
CHANGE_PW_URL = "/api/v1/auth/change-password/"
FORGOT_PW_URL = "/api/v1/auth/forgot-password/"
RESET_PW_URL = "/api/v1/auth/reset-password/"

VALID_REGISTER_PAYLOAD = {
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "StrongPass123!",
    "password_confirm": "StrongPass123!",
}


@pytest.mark.django_db
class TestRegister:
    def test_valid_registration_returns_201(self, api_client):
        res = api_client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD)
        assert res.status_code == 201
        assert "detail" in res.data

    def test_created_user_is_inactive_pending_verification(self, api_client):
        api_client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD)
        user = User.objects.get(username="newuser")
        assert user.is_active is False

    def test_verification_email_is_queued(self, api_client):
        api_client.post(REGISTER_URL, VALID_REGISTER_PAYLOAD)
        assert len(mail.outbox) == 1
        assert "newuser@example.com" in mail.outbox[0].to

    def test_duplicate_username_returns_400(self, api_client, user):
        payload = {**VALID_REGISTER_PAYLOAD, "username": user.username}
        res = api_client.post(REGISTER_URL, payload)
        assert res.status_code == 400

    def test_duplicate_email_returns_400(self, api_client, user):
        payload = {**VALID_REGISTER_PAYLOAD, "email": user.email}
        res = api_client.post(REGISTER_URL, payload)
        assert res.status_code == 400

    def test_password_mismatch_returns_400(self, api_client):
        payload = {**VALID_REGISTER_PAYLOAD, "password_confirm": "WrongPass!"}
        res = api_client.post(REGISTER_URL, payload)
        assert res.status_code == 400

    def test_missing_required_fields_returns_400(self, api_client):
        res = api_client.post(REGISTER_URL, {"username": "x"})
        assert res.status_code == 400


@pytest.mark.django_db
class TestVerifyEmail:
    def test_valid_token_activates_user_and_returns_tokens(self, api_client):
        user = UserFactory(is_active=False)
        token = make_email_verify_token(user.pk)

        res = api_client.post(VERIFY_URL, {"token": token})

        assert res.status_code == 200
        assert "access" in res.data["tokens"]
        assert "refresh" in res.data["tokens"]
        user.refresh_from_db()
        assert user.is_active is True

    def test_already_active_user_still_returns_200(self, api_client, user):
        token = make_email_verify_token(user.pk)
        res = api_client.post(VERIFY_URL, {"token": token})
        assert res.status_code == 200

    def test_invalid_token_returns_400(self, api_client):
        res = api_client.post(VERIFY_URL, {"token": "not-a-valid-token"})
        assert res.status_code == 400

    def test_expired_token_returns_400(self, api_client):
        from unittest.mock import patch
        user = UserFactory(is_active=False)
        token = signing.dumps(user.pk, salt="fittrack-email-verify")
        with patch("accounts.tokens.EMAIL_VERIFY_MAX_AGE", -1):
            res = api_client.post(VERIFY_URL, {"token": token})
        assert res.status_code == 400

    def test_missing_token_returns_400(self, api_client):
        res = api_client.post(VERIFY_URL, {})
        assert res.status_code == 400


@pytest.mark.django_db
class TestResendVerification:
    def test_always_returns_200_regardless_of_email(self, api_client):
        """Security: never reveal whether an address is registered."""
        res = api_client.post(RESEND_URL, {"email": "nobody@example.com"})
        assert res.status_code == 200

    def test_queues_email_for_inactive_user(self, api_client):
        user = UserFactory(is_active=False)
        api_client.post(RESEND_URL, {"email": user.email})
        assert len(mail.outbox) == 1

    def test_no_email_queued_for_already_active_user(self, api_client, user):
        api_client.post(RESEND_URL, {"email": user.email})
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestLogin:
    def test_active_user_receives_token_pair(self, api_client, user):
        res = api_client.post(LOGIN_URL, {"username": user.username, "password": "TestPass123!"})
        assert res.status_code == 200
        assert "access" in res.data
        assert "refresh" in res.data

    def test_inactive_user_is_rejected(self, api_client):
        user = UserFactory(is_active=False)
        res = api_client.post(LOGIN_URL, {"username": user.username, "password": "TestPass123!"})
        assert res.status_code == 401

    def test_wrong_password_returns_401(self, api_client, user):
        res = api_client.post(LOGIN_URL, {"username": user.username, "password": "WrongPass!"})
        assert res.status_code == 401

    def test_nonexistent_user_returns_401(self, api_client):
        res = api_client.post(LOGIN_URL, {"username": "ghost", "password": "pass"})
        assert res.status_code == 401


@pytest.mark.django_db
class TestTokenRefresh:
    def test_valid_refresh_token_returns_new_access_token(self, api_client, user):
        login_res = api_client.post(LOGIN_URL, {"username": user.username, "password": "TestPass123!"})
        refresh = login_res.data["refresh"]

        res = api_client.post(REFRESH_URL, {"refresh": refresh})
        assert res.status_code == 200
        assert "access" in res.data

    def test_invalid_refresh_token_returns_401(self, api_client):
        res = api_client.post(REFRESH_URL, {"refresh": "bad-token"})
        assert res.status_code == 401


@pytest.mark.django_db
class TestMeView:
    def test_get_returns_current_user_data(self, auth_client, user):
        res = auth_client.get(ME_URL)
        assert res.status_code == 200
        assert res.data["username"] == user.username
        assert res.data["email"] == user.email

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(ME_URL)
        assert res.status_code == 401

    def test_patch_updates_user_fields(self, auth_client, user):
        res = auth_client.patch(ME_URL, {"first_name": "Updated"})
        assert res.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_patch_updates_nested_profile(self, auth_client, user):
        res = auth_client.patch(ME_URL, {"profile": {"bio": "Gym rat"}}, format="json")
        assert res.status_code == 200
        user.profile.refresh_from_db()
        assert user.profile.bio == "Gym rat"


@pytest.mark.django_db
class TestChangePassword:
    def test_correct_old_password_allows_update(self, auth_client, user):
        res = auth_client.post(CHANGE_PW_URL, {
            "old_password": "TestPass123!",
            "new_password": "NewStrongPass456!",
        })
        assert res.status_code == 200
        user.refresh_from_db()
        assert user.check_password("NewStrongPass456!")

    def test_wrong_old_password_returns_400(self, auth_client):
        res = auth_client.post(CHANGE_PW_URL, {
            "old_password": "WrongOldPass!",
            "new_password": "NewStrongPass456!",
        })
        assert res.status_code == 400

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.post(CHANGE_PW_URL, {
            "old_password": "TestPass123!",
            "new_password": "NewPass!",
        })
        assert res.status_code == 401


@pytest.mark.django_db
class TestForgotPassword:
    def test_always_returns_200_regardless_of_email(self, api_client):
        """Security: never reveal whether an email is registered."""
        res = api_client.post(FORGOT_PW_URL, {"email": "ghost@example.com"})
        assert res.status_code == 200

    def test_queues_reset_email_for_active_user(self, api_client, user):
        api_client.post(FORGOT_PW_URL, {"email": user.email})
        assert len(mail.outbox) == 1

    def test_no_email_for_inactive_user(self, api_client):
        user = UserFactory(is_active=False)
        api_client.post(FORGOT_PW_URL, {"email": user.email})
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestResetPassword:
    def test_valid_token_updates_password(self, api_client, user):
        token = make_password_reset_token(user.pk)
        res = api_client.post(RESET_PW_URL, {"token": token, "new_password": "BrandNew789!"})
        assert res.status_code == 200
        user.refresh_from_db()
        assert user.check_password("BrandNew789!")

    def test_invalid_token_returns_400(self, api_client):
        res = api_client.post(RESET_PW_URL, {"token": "garbage", "new_password": "NewPass!"})
        assert res.status_code == 400

    def test_expired_token_returns_400(self, api_client, user):
        from unittest.mock import patch
        token = signing.dumps(user.pk, salt="fittrack-password-reset")
        # Patch max_age to -1 so the signature is considered expired on read.
        with patch("accounts.tokens.PASSWORD_RESET_MAX_AGE", -1):
            res = api_client.post(RESET_PW_URL, {"token": token, "new_password": "NewPass!"})
        assert res.status_code == 400
