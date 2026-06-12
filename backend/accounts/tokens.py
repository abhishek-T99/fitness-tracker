"""Stateless signed tokens for email verification and password reset.

Uses django.core.signing so no extra DB table is needed. The user's PK is
the payload; the salt separates the two token purposes so a password-reset
token can never be used to verify an email address.
"""
from datetime import timedelta

from django.core import signing

_EMAIL_VERIFY_SALT = "fittrack-email-verify"
_PASSWORD_RESET_SALT = "fittrack-password-reset"

EMAIL_VERIFY_MAX_AGE = int(timedelta(days=1).total_seconds())   # 24 h
PASSWORD_RESET_MAX_AGE = int(timedelta(hours=1).total_seconds())  # 1 h


def make_email_verify_token(user_id: int) -> str:
    return signing.dumps(user_id, salt=_EMAIL_VERIFY_SALT)


def read_email_verify_token(token: str) -> int:
    """Return user_id or raise signing.SignatureExpired / signing.BadSignature."""
    return signing.loads(token, salt=_EMAIL_VERIFY_SALT, max_age=EMAIL_VERIFY_MAX_AGE)


def make_password_reset_token(user_id: int) -> str:
    return signing.dumps(user_id, salt=_PASSWORD_RESET_SALT)


def read_password_reset_token(token: str) -> int:
    """Return user_id or raise signing.SignatureExpired / signing.BadSignature."""
    return signing.loads(token, salt=_PASSWORD_RESET_SALT, max_age=PASSWORD_RESET_MAX_AGE)
