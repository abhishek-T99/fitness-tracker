from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import reports.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FitnessReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period_type", models.CharField(choices=[("weekly", "Weekly"), ("monthly", "Monthly"), ("yearly", "Yearly")], max_length=10)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("emailed_at", models.DateTimeField(blank=True, null=True)),
                ("pdf", models.FileField(blank=True, upload_to=reports.models._report_upload_path)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fitness_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-generated_at"]},
        ),
    ]
