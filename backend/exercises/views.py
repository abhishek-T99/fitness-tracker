import hashlib

from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Exercise
from .serializers import ExerciseSerializer

LIST_CACHE_PREFIX = "exercises:list:"
LIST_CACHE_TTL = 60 * 60 * 24  # 24h — invalidated on Exercise save.


def _list_cache_key(request) -> str:
    raw = "&".join(f"{k}={v}" for k, v in sorted(request.query_params.items()))
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"{LIST_CACHE_PREFIX}{digest}"


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
