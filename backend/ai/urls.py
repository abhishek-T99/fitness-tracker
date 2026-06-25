from django.urls import path

from .views import NutritionParseView

urlpatterns = [
    path("nutrition/parse/", NutritionParseView.as_view(), name="ai-nutrition-parse"),
]
