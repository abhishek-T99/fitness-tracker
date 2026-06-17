from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserLevel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_xp", models.PositiveBigIntegerField(default=0)),
                ("level", models.PositiveIntegerField(default=1)),
                ("tier", models.CharField(choices=[("rookie","Rookie"),("amateur","Amateur"),("athlete","Athlete"),("warrior","Warrior"),("legend","Legend"),("elite","Elite"),("immortal","Immortal")], default="rookie", max_length=20)),
                ("athlete_class", models.CharField(choices=[("rookie","Rookie"),("iron_warrior","Iron Warrior"),("road_warrior","Road Warrior"),("fire_breather","Fire Breather"),("sculptor","Sculptor"),("wellness_champion","Wellness Champion")], default="rookie", max_length=30)),
                ("prestige_count", models.PositiveSmallIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="level_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "User Level"},
        ),
        migrations.CreateModel(
            name="WeeklyChallenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("week_start", models.DateField()),
                ("challenge_type", models.CharField(choices=[("complete_workouts","Complete workouts"),("log_meals","Log meals"),("log_water","Log water"),("log_measurement","Log measurement"),("record_pr","Set a PR")], max_length=30)),
                ("target_value", models.PositiveIntegerField(default=1)),
                ("xp_reward", models.PositiveIntegerField(default=200)),
                ("description", models.CharField(max_length=200)),
            ],
            options={"ordering": ["week_start", "challenge_type"], "unique_together": {("week_start", "challenge_type")}},
        ),
        migrations.CreateModel(
            name="XPTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.IntegerField(help_text="Final XP after multiplier")),
                ("base_amount", models.IntegerField(help_text="XP before multiplier")),
                ("multiplier", models.DecimalField(decimal_places=2, default=1.0, max_digits=4)),
                ("reason", models.CharField(max_length=200)),
                ("source_type", models.CharField(choices=[("workout","Workout"),("personal_record","Personal Record"),("nutrition","Nutrition"),("measurement","Measurement"),("goal","Goal"),("achievement","Achievement"),("social","Social"),("challenge","Challenge"),("streak_bonus","Streak Bonus")], max_length=30)),
                ("source_id", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="xp_transactions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="UserWeeklyChallenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("current_value", models.PositiveIntegerField(default=0)),
                ("completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("challenge", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_progress", to="levels.weeklychallenge")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="weekly_challenges", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["challenge__challenge_type"], "unique_together": {("user", "challenge")}},
        ),
        migrations.AddIndex(
            model_name="xptransaction",
            index=models.Index(fields=["user", "-created_at"], name="levels_xptr_user_id_idx"),
        ),
        migrations.AddIndex(
            model_name="xptransaction",
            index=models.Index(fields=["user", "source_type"], name="levels_xptr_source_idx"),
        ),
    ]
