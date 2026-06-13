import hashlib

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Exercise
from .serializers import ExerciseSerializer
from .youtube import YouTubeError, fetch_tutorials

LIST_CACHE_PREFIX = "exercises:list:"
LIST_CACHE_TTL = 60 * 60 * 24  # 24h — invalidated on Exercise save.


def _list_cache_key(request) -> str:
    raw = "&".join(f"{k}={v}" for k, v in sorted(request.query_params.items()))
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"{LIST_CACHE_PREFIX}{digest}"


@extend_schema(tags=["Exercises"])
class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only exercise library.

    The library is small + static, but the workout editor hits this endpoint
    on every keystroke. We cache the serialized list response per
    query-string for 24h and invalidate everything on Exercise.save() via a
    `cache.delete_pattern` in the model signal.
    """

    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Exercise.objects.all()
    filterset_fields = ["category", "primary_muscle", "equipment", "is_compound"]
    search_fields = ["name", "instructions"]
    ordering_fields = ["name", "category"]
    lookup_field = "slug"

    def list(self, request, *args, **kwargs):
        key = _list_cache_key(request)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, LIST_CACHE_TTL)
        return response


@extend_schema(tags=["Exercises"])
class YouTubeTutorialsView(APIView):
    """
    GET /api/v1/exercises/youtube-tutorials/?exercise_slug=bench-press

    Returns up to 4 YouTube tutorial videos for the given exercise,
    sorted by view count descending.  Results are cached in Redis for 24 h.

    Requires YOUTUBE_API_KEY to be set in settings; returns 503 otherwise.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        slug = request.query_params.get("exercise_slug", "").strip()
        if not slug:
            return Response(
                {"detail": "exercise_slug query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            exercise = Exercise.objects.get(slug=slug)
        except Exercise.DoesNotExist:
            return Response(
                {"detail": "Exercise not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        api_key = getattr(settings, "YOUTUBE_API_KEY", "")
        if not api_key:
            return Response(
                {"detail": "YouTube integration is not configured on this server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            videos = fetch_tutorials(exercise.youtube_search_query)
        except YouTubeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"videos": videos})
