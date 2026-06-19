from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FitnessReport
from .serializers import FitnessReportSerializer
from .tasks import generate_and_email_report


@extend_schema(
    tags=["Reports"],
    summary="List the current user's fitness reports",
    responses=FitnessReportSerializer(many=True),
)
class ReportListView(generics.ListAPIView):
    serializer_class = FitnessReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FitnessReport.objects.filter(user=self.request.user)


@extend_schema(
    tags=["Reports"],
    summary="Trigger an on-demand fitness report",
    request=inline_serializer(
        name="TriggerReportRequest",
        fields={"period_type": serializers.ChoiceField(choices=["weekly", "monthly", "yearly"])},
    ),
    responses={
        202: inline_serializer(
            name="TriggerReportResponse",
            fields={"detail": serializers.CharField()},
        ),
        400: inline_serializer(
            name="TriggerReportError",
            fields={"detail": serializers.CharField()},
        ),
    },
)
class TriggerReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        period_type = request.data.get("period_type", "")
        valid = {c[0] for c in FitnessReport.PeriodType.choices}
        if period_type not in valid:
            return Response(
                {"detail": f"period_type must be one of: {', '.join(sorted(valid))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        generate_and_email_report.delay(request.user.pk, period_type)
        return Response(
            {"detail": f"Your {period_type} report is being generated and will be emailed shortly."},
            status=status.HTTP_202_ACCEPTED,
        )
