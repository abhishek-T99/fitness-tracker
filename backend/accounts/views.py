from django.contrib.auth import get_user_model
from django.core import signing
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView as _TokenObtainPairView,
    TokenRefreshView as _TokenRefreshView,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .social import SocialAuthError, verify_facebook_token, verify_google_token
from .tasks import send_password_reset_email, send_verification_email
from .tokens import (
    make_email_verify_token,
    make_password_reset_token,
    read_email_verify_token,
    read_password_reset_token,
)

User = get_user_model()


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


# Thin wrappers so we can attach tags without mutating the library classes.
# authentication_classes=[] is intentional: these are public endpoints and must
# not run JWT auth. A stale token in the browser would otherwise cause
# JWTAuthentication to raise AuthenticationFailed before AllowAny can permit
# the request, blocking login/register for users with old sessions.
@extend_schema(tags=["Auth"], auth=[])
class TokenObtainPairView(_TokenObtainPairView):
    authentication_classes = []


@extend_schema(tags=["Auth"], auth=[])
class TokenRefreshView(_TokenRefreshView):
    authentication_classes = []


@extend_schema(
    tags=["Auth"],
    auth=[],
    request=RegisterSerializer,
    responses={
        201: inline_serializer(
            name="RegisterResponse",
            fields={"detail": serializers.CharField()},
        ),
    },
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = make_email_verify_token(user.pk)
        send_verification_email.delay(user.pk, token)
        return Response(
            {"detail": "Account created. Check your email to verify your account."},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Auth"],
    auth=[],
    request=inline_serializer(
        name="VerifyEmailRequest",
        fields={"token": serializers.CharField()},
    ),
    responses={
        200: inline_serializer(
            name="VerifyEmailResponse",
            fields={
                "user": UserSerializer(),
                "tokens": inline_serializer(
                    name="TokenPair",
                    fields={
                        "access": serializers.CharField(),
                        "refresh": serializers.CharField(),
                    },
                ),
            },
        ),
        400: inline_serializer(
            name="VerifyEmailError",
            fields={"detail": serializers.CharField()},
        ),
    },
)
class VerifyEmailView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token", "")
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = read_email_verify_token(token)
        except signing.SignatureExpired:
            return Response(
                {"detail": "Verification link has expired. Request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = get_object_or_404(User, pk=user_id)
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        return Response({"user": UserSerializer(user).data, "tokens": tokens_for(user)})


@extend_schema(
    tags=["Auth"],
    auth=[],
    request=ResendVerificationSerializer,
    responses={
        200: inline_serializer(
            name="ResendVerificationResponse",
            fields={"detail": serializers.CharField()},
        ),
    },
)
class ResendVerificationView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email__iexact=email, is_active=False)
            token = make_email_verify_token(user.pk)
            send_verification_email.delay(user.pk, token)
        except User.DoesNotExist:
            pass  # don't reveal whether address exists or is already verified
        return Response(
            {"detail": "If that email is pending verification, a new link is on its way."}
        )


@extend_schema(
    tags=["Auth"],
    auth=[],
    request=ForgotPasswordSerializer,
    responses={
        200: inline_serializer(
            name="ForgotPasswordResponse",
            fields={"detail": serializers.CharField()},
        ),
    },
)
class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            token = make_password_reset_token(user.pk)
            send_password_reset_email.delay(user.pk, token)
        except User.DoesNotExist:
            pass  # don't reveal whether email is registered
        return Response(
            {"detail": "If that email is registered, a reset link is on its way."}
        )


@extend_schema(
    tags=["Auth"],
    auth=[],
    request=ResetPasswordSerializer,
    responses={
        200: inline_serializer(
            name="ResetPasswordResponse",
            fields={"detail": serializers.CharField()},
        ),
        400: inline_serializer(
            name="ResetPasswordError",
            fields={"detail": serializers.CharField()},
        ),
    },
)
class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]
        try:
            user_id = read_password_reset_token(token)
        except signing.SignatureExpired:
            return Response(
                {"detail": "Reset link has expired. Request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = get_object_or_404(User, pk=user_id, is_active=True)
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated. You can now sign in."})


@extend_schema_view(
    get=extend_schema(tags=["Auth"], responses=UserSerializer),
    put=extend_schema(tags=["Auth"], request=UserUpdateSerializer, responses=UserSerializer),
    patch=extend_schema(tags=["Auth"], request=UserUpdateSerializer, responses=UserSerializer),
)
class MeView(generics.RetrieveUpdateAPIView):
    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserSerializer(instance).data)


# ---------------------------------------------------------------------------
# Social auth
# ---------------------------------------------------------------------------

def _unique_username(email: str) -> str:
    """Derive a unique username from the email local part."""
    base = email.split("@")[0][:140] or "user"
    username = base
    suffix = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


def _get_or_create_social_user(info: dict) -> User:
    """Link by verified email, or provision a new active account.

    The provider has verified ownership of the email, so:
      - an existing unverified (inactive) account with the same address is
        safe to activate, and
      - new accounts skip the email-verification flow entirely.
    """
    user = User.objects.filter(email__iexact=info["email"]).first()
    if user:
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        return user
    user = User(
        username=_unique_username(info["email"]),
        email=info["email"],
        first_name=info.get("first_name", ""),
        last_name=info.get("last_name", ""),
        is_active=True,
    )
    user.set_unusable_password()  # social-only account — no password login
    user.save()
    return user


class SocialLoginView(APIView):
    """Base: POST {token} → verify with provider → respond {user, tokens}."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def verify(self, token: str) -> dict:  # pragma: no cover — overridden
        raise NotImplementedError

    def post(self, request):
        token = request.data.get("token", "")
        if not token:
            return Response(
                {"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            info = self.verify(token)
        except SocialAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        user = _get_or_create_social_user(info)
        return Response({"user": UserSerializer(user).data, "tokens": tokens_for(user)})


_SOCIAL_SCHEMA = dict(
    tags=["Auth"],
    auth=[],
    request=inline_serializer(
        name="SocialLoginRequest",
        fields={"token": serializers.CharField()},
    ),
    responses={
        200: inline_serializer(
            name="SocialLoginResponse",
            fields={
                "user": UserSerializer(),
                "tokens": inline_serializer(
                    name="SocialTokenPair",
                    fields={
                        "access": serializers.CharField(),
                        "refresh": serializers.CharField(),
                    },
                ),
            },
        ),
        401: inline_serializer(
            name="SocialLoginError",
            fields={"detail": serializers.CharField()},
        ),
    },
)


@extend_schema(summary="Sign in with a Google ID token", **_SOCIAL_SCHEMA)
class GoogleLoginView(SocialLoginView):
    def verify(self, token):
        # Resolved at call time so tests can patch accounts.views.verify_google_token
        return verify_google_token(token)


@extend_schema(summary="Sign in with a Facebook access token", **_SOCIAL_SCHEMA)
class FacebookLoginView(SocialLoginView):
    def verify(self, token):
        return verify_facebook_token(token)


@extend_schema(
    tags=["Auth"],
    request=ChangePasswordSerializer,
    responses={
        200: inline_serializer(
            name="ChangePasswordResponse",
            fields={"detail": serializers.CharField()},
        ),
        400: inline_serializer(
            name="ChangePasswordError",
            fields={"old_password": serializers.CharField()},
        ),
    },
)
class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password updated."})
