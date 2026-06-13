from django.urls import path

from .views import (
    IntegrationListView,
    StravaCallbackView,
    StravaConnectView,
    StravaDisconnectView,
    StravaWebhookView,
    IntervalsConnectView,
    IntervalsDisconnectView,
    IntervalsSyncView,
    IntervalsWebhookView,
)

urlpatterns = [
    path("", IntegrationListView.as_view(), name="integration-list"),
    # Strava
    path("strava/connect/", StravaConnectView.as_view(), name="strava-connect"),
    path("strava/callback/", StravaCallbackView.as_view(), name="strava-callback"),
    path("strava/disconnect/", StravaDisconnectView.as_view(), name="strava-disconnect"),
    path("strava/webhook/", StravaWebhookView.as_view(), name="strava-webhook"),
    # Intervals.icu
    path("intervals/connect/", IntervalsConnectView.as_view(), name="intervals-connect"),
    path("intervals/disconnect/", IntervalsDisconnectView.as_view(), name="intervals-disconnect"),
    path("intervals/sync/", IntervalsSyncView.as_view(), name="intervals-sync"),
    path("intervals/webhook/", IntervalsWebhookView.as_view(), name="intervals-webhook"),
]
