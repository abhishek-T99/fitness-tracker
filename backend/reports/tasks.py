"""Celery tasks for fitness report generation and dispatch."""
import logging
from datetime import date, timedelta
from io import BytesIO

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


def _period_bounds(period_type: str, ref_date: date | None = None) -> tuple[date, date]:
    """Return (period_start, period_end) for the completed period just before ref_date."""
    today = ref_date or date.today()
    if period_type == "weekly":
        end = today - timedelta(days=today.weekday() + 1)   # last Sunday
        start = end - timedelta(days=6)                      # last Monday
    elif period_type == "monthly":
        first_of_month = today.replace(day=1)
        end = first_of_month - timedelta(days=1)             # last day of prev month
        start = end.replace(day=1)                           # first day of prev month
    elif period_type == "yearly":
        prev_year = today.year - 1
        start = date(prev_year, 1, 1)
        end   = date(prev_year, 12, 31)
    else:
        raise ValueError(f"Unknown period_type: {period_type!r}")
    return start, end


@shared_task(
    ignore_result=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_and_email_report(user_id: int, period_type: str, ref_date_iso: str | None = None):
    """Generate a PDF fitness report for one user and email it."""
    from .models import FitnessReport
    from .pdf_generator import generate_pdf
    from .report_service import collect_report_data

    try:
        user = User.objects.select_related("profile").get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        logger.warning("generate_and_email_report: user %s not found or inactive", user_id)
        return

    ref_date = date.fromisoformat(ref_date_iso) if ref_date_iso else None
    period_start, period_end = _period_bounds(period_type, ref_date)

    logger.info(
        "Generating %s report for user %s (%s – %s)",
        period_type, user.username, period_start, period_end,
    )

    # Collect stats and build PDF
    report_data = collect_report_data(user, period_start, period_end)
    pdf_bytes   = generate_pdf(report_data, period_type)

    # Persist the report record
    filename = f"fittrack_{period_type}_{period_start}_{period_end}.pdf"
    report = FitnessReport(
        user=user,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
    )
    report.pdf.save(filename, ContentFile(pdf_bytes), save=False)
    report.save()

    # Email
    _send_report_email(user, report, pdf_bytes, period_type, period_start, period_end)

    # Stamp last_report_sent_at on the profile
    profile = getattr(user, "profile", None)
    if profile:
        profile.last_report_sent_at = timezone.now()
        profile.save(update_fields=["last_report_sent_at"])

    report.emailed_at = timezone.now()
    report.save(update_fields=["emailed_at"])

    logger.info("Report sent to user %s (report_id=%s)", user.username, report.pk)
    return report.pk


def _send_report_email(user, report, pdf_bytes: bytes, period_type, period_start, period_end):
    name = user.first_name or user.username
    label = period_type.capitalize()
    date_range = f"{period_start.strftime('%b %d')} – {period_end.strftime('%b %d, %Y')}"

    subject = f"Your FitTrack {label} Fitness Report – {date_range}"

    plain = (
        f"Hi {name},\n\n"
        f"Your {label.lower()} FitTrack fitness report for {date_range} is attached.\n\n"
        f"Keep up the great work!\n\n"
        f"— The FitTrack Team"
    )

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f8fafc;margin:0;padding:32px;">
  <div style="max-width:520px;margin:auto;background:#fff;border-radius:12px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <div style="background:#6366f1;border-radius:8px;padding:24px;text-align:center;margin-bottom:24px;">
      <h1 style="color:#fff;font-size:22px;margin:0;">FitTrack</h1>
      <p style="color:#c7d2fe;margin:4px 0 0;">{label} Fitness Report</p>
    </div>
    <h2 style="color:#1e293b;font-size:18px;">Hi {name}!</h2>
    <p style="color:#475569;line-height:1.6;">
      Your {label.lower()} fitness report for <strong>{date_range}</strong> is ready.
      It's attached to this email as a PDF — open it to see your full breakdown:
    </p>
    <ul style="color:#475569;line-height:1.8;">
      <li>Workout summary &amp; training volume</li>
      <li>Nutrition overview &amp; macro averages</li>
      <li>Body composition changes</li>
      <li>Goals progress</li>
      <li>Achievements unlocked</li>
    </ul>
    <p style="color:#475569;line-height:1.6;">
      You can change your report frequency or disable these emails in your
      <a href="{settings.FRONTEND_URL}/profile" style="color:#6366f1;">account settings</a>.
    </p>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">
      &copy; FitTrack — helping you reach your fitness goals.
    </p>
  </div>
</body>
</html>
"""

    msg = EmailMessage(
        subject=subject,
        body=plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.content_subtype = "html"
    msg.body = html
    msg.attach(
        f"fittrack_report_{period_start}.pdf",
        pdf_bytes,
        "application/pdf",
    )
    msg.send(fail_silently=False)


# ── Beat dispatch tasks ───────────────────────────────────────────────────────

@shared_task(ignore_result=True)
def dispatch_weekly_reports():
    """Queue weekly reports for all opted-in users. Runs every Monday."""
    _dispatch_reports("weekly")


@shared_task(ignore_result=True)
def dispatch_monthly_reports():
    """Queue monthly reports for all opted-in users. Runs 1st of each month."""
    _dispatch_reports("monthly")


@shared_task(ignore_result=True)
def dispatch_yearly_reports():
    """Queue yearly reports for all opted-in users. Runs Jan 1."""
    _dispatch_reports("yearly")


def _dispatch_reports(period_type: str):
    users = User.objects.filter(
        is_active=True,
        profile__reports_enabled=True,
        profile__report_frequency=period_type,
    ).values_list("id", flat=True)

    queued = 0
    for user_id in users:
        generate_and_email_report.delay(user_id, period_type)
        queued += 1

    logger.info("dispatch_%s_reports: queued %d reports", period_type, queued)
    return queued
