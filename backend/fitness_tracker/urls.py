"""Root URL routes for the fitness_tracker project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

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
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
