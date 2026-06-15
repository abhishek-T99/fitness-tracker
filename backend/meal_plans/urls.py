from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MealPlanItemViewSet, MealPlanViewSet, StandaloneMealPlanItemViewSet

router = DefaultRouter()
router.register("meal-plans", MealPlanViewSet, basename="meal-plan")
router.register("meal-plan-items", StandaloneMealPlanItemViewSet, basename="meal-plan-item")

urlpatterns = router.urls + [
    # Nested items: /meal-plans/{plan_pk}/items/
    path(
        "meal-plans/<int:plan_pk>/items/",
        MealPlanItemViewSet.as_view({"get": "list", "post": "create"}),
        name="meal-plan-items-list",
    ),
    path(
        "meal-plans/<int:plan_pk>/items/<int:pk>/",
        MealPlanItemViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="meal-plan-items-detail",
    ),
]
