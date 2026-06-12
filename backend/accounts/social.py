"""
Social-provider token verification.

Each verifier takes the raw token the frontend obtained from the provider's
JS SDK, validates it server-side against the provider, and returns a
normalized dict: {"email", "first_name", "last_name"}.

Raises SocialAuthError for anything that should not produce a session:
invalid/expired tokens, tokens minted for another app, unverified or
missing email addresses.
"""
import requests
from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

FACEBOOK_GRAPH = "https://graph.facebook.com/v19.0"


class SocialAuthError(Exception):
    """Token failed verification — caller should respond 401."""


def verify_google_token(token: str) -> dict:
    """Validate a Google ID token (from Google Identity Services)."""
    try:
        payload = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError as exc:
        raise SocialAuthError("Invalid Google token.") from exc

    if not payload.get("email_verified"):
        raise SocialAuthError("Google account email is not verified.")

    return {
        "email": payload["email"],
        "first_name": payload.get("given_name", ""),
        "last_name": payload.get("family_name", ""),
    }


def verify_facebook_token(token: str) -> dict:
    """Validate a Facebook access token (from the FB JS SDK).

    Two Graph API calls:
      1. /debug_token with our app token — proves the token is valid AND was
         issued for *our* app (a valid token stolen from another FB app must
         not log anyone in here).
      2. /me — fetch the profile fields we need.
    """
    app_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
    debug = requests.get(
        f"{FACEBOOK_GRAPH}/debug_token",
        params={"input_token": token, "access_token": app_token},
        timeout=10,
    ).json()

    data = debug.get("data", {})
    if not data.get("is_valid"):
        raise SocialAuthError("Invalid Facebook token.")
    if data.get("app_id") != settings.FACEBOOK_APP_ID:
        raise SocialAuthError("Facebook token was issued for another app.")

    profile = requests.get(
        f"{FACEBOOK_GRAPH}/me",
        params={"fields": "id,email,first_name,last_name", "access_token": token},
        timeout=10,
    ).json()

    email = profile.get("email")
    if not email:
        # User declined the email permission — we can't link an account.
        raise SocialAuthError(
            "Your Facebook account did not share an email address."
        )

    return {
        "email": email,
        "first_name": profile.get("first_name", ""),
        "last_name": profile.get("last_name", ""),
    }
