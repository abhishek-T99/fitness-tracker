from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AchievementCatalogViewSet, StreakView, UserAchievementViewSet

router = DefaultRouter()
router.register("catalog", AchievementCatalogViewSet, basename="achievement-catalog")
router.register("unlocked", UserAchievementViewSet, basename="user-achievement")

urlpatterns = router.urls + [
    path("streak/", StreakView.as_view(), name="streak"),
]
