from rest_framework import serializers

from .models import FitnessReport


class FitnessReportSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = FitnessReport
        fields = [
            "id",
            "period_type",
            "period_start",
            "period_end",
            "generated_at",
            "emailed_at",
            "pdf_url",
        ]
        read_only_fields = fields

    def get_pdf_url(self, obj):
        if not obj.pdf:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.pdf.url) if request else obj.pdf.url
