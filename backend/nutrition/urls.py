from rest_framework.routers import DefaultRouter

from .views import FoodViewSet, MealViewSet, WaterLogViewSet

router = DefaultRouter()
router.register("foods", FoodViewSet, basename="food")
router.register("meals", MealViewSet, basename="meal")
router.register("water", WaterLogViewSet, basename="water")

urlpatterns = router.urls
