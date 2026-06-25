"""Shared QuerySet bases used across user-scoped apps.

Every domain model owned by a user (Workout, Meal, BodyMeasurement, Goal, ...)
filters the same way in ViewSet.get_queryset(): ``.filter(user=request.user)``.
``UserOwnedQuerySet.for_user(user)`` centralizes that filter so views read as
``Model.objects.for_user(self.request.user).prefetch_related(...)``.

Adopt incrementally — models without a ``user`` FK won't benefit.
"""
from __future__ import annotations

from django.db import models


class UserOwnedQuerySet(models.QuerySet):
    """QuerySet for models with a ``user`` ForeignKey to AUTH_USER_MODEL."""

    def for_user(self, user) -> "UserOwnedQuerySet":
        """Scope the queryset to a single user."""
        return self.filter(user=user)
