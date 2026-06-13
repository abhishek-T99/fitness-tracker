from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ExerciseViewSet, YouTubeTutorialsView

router = DefaultRouter()
router.register("", ExerciseViewSet, basename="exercise")

urlpatterns = [
    # Must come before router.urls — the viewset's slug pattern would otherwise
    # try to look up "youtube-tutorials" as an exercise slug.
    path("youtube-tutorials/", YouTubeTutorialsView.as_view(), name="exercise-youtube-tutorials"),
] + router.urls
