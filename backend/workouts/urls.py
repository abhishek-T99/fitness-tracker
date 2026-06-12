from rest_framework.routers import DefaultRouter

from .views import RoutineViewSet, WorkoutViewSet

router = DefaultRouter()
router.register("routines", RoutineViewSet, basename="routine")
router.register("", WorkoutViewSet, basename="workout")

urlpatterns = router.urls
