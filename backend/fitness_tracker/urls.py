"""Root URL routes for the fitness_tracker project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

api_v1 = [
    path("auth/", include("accounts.urls")),
    path("exercises/", include("exercises.urls")),
    path("workouts/", include("workouts.urls")),
    path("nutrition/", include("nutrition.urls")),
    path("measurements/", include("measurements.urls")),
    path("goals/", include("goals.urls")),
    path("social/", include("social.urls")),
    path("achievements/", include("achievements.urls")),
    path("reminders/", include("reminders.urls")),
    path("notifications/", include("notifications.urls")),
    path("integrations/", include("integrations.urls")),
    path("", include("meal_plans.urls")),
    path("levels/", include("levels.urls")),
    path("reports/", include("reports.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
