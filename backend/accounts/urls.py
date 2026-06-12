from django.urls import path

from .views import (
    ChangePasswordView,
    FacebookLoginView,
    ForgotPasswordView,
    GoogleLoginView,
    MeView,
    RegisterView,
    ResendVerificationView,
    ResetPasswordView,
    TokenObtainPairView,
    TokenRefreshView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend_verification"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
    path("facebook/", FacebookLoginView.as_view(), name="facebook_login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
]
