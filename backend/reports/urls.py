from django.urls import path

from .views import ReportListView, TriggerReportView

urlpatterns = [
    path("", ReportListView.as_view(), name="report-list"),
    path("trigger/", TriggerReportView.as_view(), name="report-trigger"),
]
