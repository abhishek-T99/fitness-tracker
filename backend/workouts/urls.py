from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ExerciseHistoryView, RoutineViewSet, WorkoutViewSet

router = DefaultRouter()
router.register("routines", RoutineViewSet, basename="routine")
router.register("", WorkoutViewSet, basename="workout")

urlpatterns = [
    # Custom views must come before router.urls so they aren't swallowed
    # by the WorkoutViewSet's {pk} pattern (which matches any non-slash string).
    path("exercise-history/", ExerciseHistoryView.as_view(), name="exercise-history"),
] + router.urls
