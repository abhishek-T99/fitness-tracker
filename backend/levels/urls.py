from django.urls import path

from .views import ChallengesView, LeaderboardView, LevelProfileView, PrestigeView, XPTransactionListView

urlpatterns = [
    path("profile/",      LevelProfileView.as_view(),      name="level-profile"),
    path("transactions/", XPTransactionListView.as_view(), name="level-transactions"),
    path("challenges/",   ChallengesView.as_view(),        name="level-challenges"),
    path("leaderboard/",  LeaderboardView.as_view(),       name="level-leaderboard"),
    path("prestige/",     PrestigeView.as_view(),          name="level-prestige"),
]
