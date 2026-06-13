"""
ActivityTrackingMiddleware

Updates Profile.last_activity on every authenticated API request.
Throttled to one DB write per user per 5 minutes so high-traffic users
don't generate excessive database load.
"""
from datetime import timedelta

from django.utils import timezone


class ActivityTrackingMiddleware:
    THROTTLE_SECONDS = 300  # write at most once every 5 minutes per user

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._record(request)
        return response

    def _record(self, request):
        # Only track authenticated users making API requests.
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return
        if not request.path.startswith("/api/"):
            return

        try:
            profile = user.profile
        except Exception:
            return

        now = timezone.now()
        threshold = now - timedelta(seconds=self.THROTTLE_SECONDS)

        # Skip the DB write if we updated recently.
        if profile.last_activity and profile.last_activity > threshold:
            return

        # Use update() to avoid triggering updated_at auto_now and signals.
        from .models import Profile
        Profile.objects.filter(pk=profile.pk).update(last_activity=now)
        # Keep the in-memory object in sync so the same request doesn't write again.
        profile.last_activity = now
