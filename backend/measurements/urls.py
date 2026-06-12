from rest_framework.routers import DefaultRouter

from .views import BodyMeasurementViewSet

router = DefaultRouter()
router.register("", BodyMeasurementViewSet, basename="measurement")

urlpatterns = router.urls
