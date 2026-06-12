"""Weekly per-user progress summary — runs Mondays via Beat.

The output is cached so the Dashboard / Profile can surface it cheaply
without recomputing aggregates on every request.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

WEEKLY_SUMMARY_CACHE_TTL = 60 * 60 * 24 * 8  # one week + slack


def weekly_summary_cache_key(user_id: int) -> str:
    return f"weekly_summary:{user_id}"


@shared_task(ignore_result=True)
def build_weekly_summaries():
    """Build last-week stats for every active user and cache them."""
    from workouts.models import Workout

    User = get_user_model()
    now = timezone.now()
    week_start = now - timedelta(days=7)
    built = 0
    for user_id in User.objects.filter(is_active=True).values_list("id", flat=True):
        agg = Workout.objects.filter(
            user_id=user_id,
            status=Workout.Status.COMPLETED,
            started_at__gte=week_start,
        ).aggregate(
            workouts=Sum("duration_min"),
            minutes=Sum("duration_min"),
            calories=Sum("calories_burned"),
        )
        payload = {
            "generated_at": now.isoformat(),
            "workouts": agg["workouts"] or 0,
            "minutes": agg["minutes"] or 0,
            "calories": agg["calories"] or 0,
        }
        cache.set(weekly_summary_cache_key(user_id), payload, WEEKLY_SUMMARY_CACHE_TTL)
        built += 1
    logger.info("build_weekly_summaries: cached %d user summaries", built)
    return built


@shared_task(ignore_result=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_verification_email(user_id: int, token: str):
    """Send an account-activation email with a signed verification link."""
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("send_verification_email: user %s not found", user_id)
        return

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    link = f"{frontend_url}/verify-email?token={token}"
    name = user.first_name or user.username

    subject = "Verify your FitTrack account"
    plain = (
        f"Hi {name},\n\n"
        f"Thanks for signing up! Click the link below to activate your account:\n\n"
        f"{link}\n\n"
        f"This link expires in 24 hours.\n\n"
        f"If you didn't create an account, you can ignore this email.\n\n"
        f"— The FitTrack Team"
    )
    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f8fafc;margin:0;padding:32px;">
  <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <h1 style="color:#0f172a;font-size:22px;margin-top:0;">Welcome to FitTrack, {name}!</h1>
    <p style="color:#475569;line-height:1.6;">
      Thanks for signing up. Click the button below to verify your email address
      and activate your account.
    </p>
    <p style="text-align:center;margin:32px 0;">
      <a href="{link}"
         style="background:#6366f1;color:#fff;text-decoration:none;
                padding:14px 28px;border-radius:8px;font-weight:600;
                display:inline-block;">
        Verify my email
      </a>
    </p>
    <p style="color:#94a3b8;font-size:13px;">
      This link expires in 24 hours. If you didn't create an account you can
      safely ignore this email.
    </p>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">
      &copy; FitTrack — helping you reach your fitness goals.
    </p>
  </div>
</body>
</html>
"""
    send_mail(
        subject=subject,
        message=plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html,
        fail_silently=False,
    )
    logger.info("send_verification_email: sent to user %s", user_id)


@shared_task(ignore_result=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_password_reset_email(user_id: int, token: str):
    """Send a password-reset email with a signed reset link."""
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("send_password_reset_email: user %s not found", user_id)
        return

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    link = f"{frontend_url}/reset-password?token={token}"
    name = user.first_name or user.username

    subject = "Reset your FitTrack password"
    plain = (
        f"Hi {name},\n\n"
        f"We received a request to reset the password for your FitTrack account.\n\n"
        f"Click the link below to choose a new password:\n\n"
        f"{link}\n\n"
        f"This link expires in 1 hour.\n\n"
        f"If you didn't request a password reset, you can ignore this email — "
        f"your password won't be changed.\n\n"
        f"— The FitTrack Team"
    )
    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f8fafc;margin:0;padding:32px;">
  <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <h1 style="color:#0f172a;font-size:22px;margin-top:0;">Reset your password</h1>
    <p style="color:#475569;line-height:1.6;">
      Hi {name}, we received a request to reset the password for your FitTrack
      account. Click the button below to choose a new password.
    </p>
    <p style="text-align:center;margin:32px 0;">
      <a href="{link}"
         style="background:#6366f1;color:#fff;text-decoration:none;
                padding:14px 28px;border-radius:8px;font-weight:600;
                display:inline-block;">
        Reset my password
      </a>
    </p>
    <p style="color:#94a3b8;font-size:13px;">
      This link expires in 1 hour. If you didn't request a password reset,
      you can safely ignore this email — your password won't change.
    </p>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">
      &copy; FitTrack — helping you reach your fitness goals.
    </p>
  </div>
</body>
</html>
"""
    send_mail(
        subject=subject,
        message=plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html,
        fail_silently=False,
    )
    logger.info("send_password_reset_email: sent to user %s", user_id)
