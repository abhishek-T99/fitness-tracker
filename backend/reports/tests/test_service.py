"""Tests for the report data-collection service."""
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="svc_user", password="pw", email="svc@test.com", is_active=True
    )
    from accounts.models import Profile
    Profile.objects.filter(user=u).update(
        daily_calorie_goal=2000,
        weekly_workout_goal=4,
        height_cm=175,
        units="metric",
    )
    u.refresh_from_db()
    return u


@pytest.fixture
def period():
    end   = date.today()
    start = end - timedelta(days=6)
    return start, end


@pytest.mark.django_db
class TestCollectReportData:
    def test_returns_all_sections(self, user, period):
        from reports.report_service import collect_report_data

        data = collect_report_data(user, *period)
        assert set(data.keys()) >= {"workout", "nutrition", "body", "goals", "achievements", "streak"}

    def test_empty_user_returns_zeros(self, user, period):
        from reports.report_service import collect_report_data

        data = collect_report_data(user, *period)
        assert data["workout"]["count"] == 0
        assert data["nutrition"]["logged_days"] == 0
        assert data["achievements"]["new_count"] == 0
        assert data["streak"]["current"] == 0

    def test_counts_workouts_in_period(self, user, period):
        from workouts.models import Workout
        from reports.report_service import collect_report_data

        start, end = period
        Workout.objects.create(
            user=user,
            started_at=timezone.make_aware(
                timezone.datetime.combine(start, timezone.datetime.min.time())
            ),
            duration_min=60,
            calories_burned=400,
            status=Workout.Status.COMPLETED,
        )
        data = collect_report_data(user, start, end)
        assert data["workout"]["count"] == 1
        assert data["workout"]["total_minutes"] == 60
        assert data["workout"]["total_calories"] == 400

    def test_ignores_workouts_outside_period(self, user, period):
        from workouts.models import Workout
        from reports.report_service import collect_report_data

        start, end = period
        outside_date = start - timedelta(days=5)
        Workout.objects.create(
            user=user,
            started_at=timezone.make_aware(
                timezone.datetime.combine(outside_date, timezone.datetime.min.time())
            ),
            duration_min=45,
            status=Workout.Status.COMPLETED,
        )
        data = collect_report_data(user, start, end)
        assert data["workout"]["count"] == 0

    def test_ignores_draft_workouts(self, user, period):
        from workouts.models import Workout
        from reports.report_service import collect_report_data

        start, end = period
        Workout.objects.create(
            user=user,
            started_at=timezone.make_aware(
                timezone.datetime.combine(start, timezone.datetime.min.time())
            ),
            duration_min=30,
            status=Workout.Status.DRAFT,
        )
        data = collect_report_data(user, start, end)
        assert data["workout"]["count"] == 0

    def test_nutrition_aggregates_correctly(self, user, period):
        from nutrition.models import Food, Meal, MealItem
        from reports.report_service import collect_report_data

        start, end = period
        food = Food.objects.create(
            name="Test Food", calories=500, protein_g=30, carbs_g=60, fat_g=10,
        )
        meal = Meal.objects.create(
            user=user,
            meal_type=Meal.MealType.LUNCH,
            consumed_at=timezone.make_aware(
                timezone.datetime.combine(start, timezone.datetime.min.time())
            ),
        )
        MealItem.objects.create(meal=meal, food=food, servings=1)

        data = collect_report_data(user, start, end)
        assert data["nutrition"]["logged_days"] == 1
        assert data["nutrition"]["avg_calories"] == 500.0

    def test_weight_change_computed(self, user, period):
        from measurements.models import BodyMeasurement
        from reports.report_service import collect_report_data

        start, end = period
        BodyMeasurement.objects.create(user=user, recorded_at=start, weight_kg=80.0)
        BodyMeasurement.objects.create(user=user, recorded_at=end,   weight_kg=79.0)

        data = collect_report_data(user, start, end)
        assert data["body"]["weight_change"] == -1.0

    def test_goal_progress_included(self, user, period):
        from goals.models import Goal
        from reports.report_service import collect_report_data

        Goal.objects.create(
            user=user, title="Lose 5kg", goal_type=Goal.Type.WEIGHT_LOSS,
            target_value=70, current_value=73, starting_value=80,
            status=Goal.Status.ACTIVE,
        )
        data = collect_report_data(user, *period)
        assert data["goals"]["active_count"] == 1
        assert len(data["goals"]["active_goals"]) == 1
        assert data["goals"]["active_goals"][0]["title"] == "Lose 5kg"

    def test_achievements_in_period(self, user, period):
        from achievements.models import Achievement, UserAchievement
        from reports.report_service import collect_report_data

        start, end = period
        ach = Achievement.objects.create(
            code="first_workout", name="First Workout", description="...",
            kind=Achievement.Kind.WORKOUT_COUNT, threshold=1,
        )
        UserAchievement.objects.create(user=user, achievement=ach)

        data = collect_report_data(user, start, end)
        assert data["achievements"]["new_count"] == 1
        assert "First Workout" in data["achievements"]["new_badges"]
