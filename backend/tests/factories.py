"""
factory-boy factories for every domain model.

Convention
----------
- Factories create self-contained objects with sensible defaults.
- Foreign keys use SubFactory so a factory can be used standalone.
- Sequences guarantee uniqueness for fields with unique constraints.
- Pass explicit values to override any default:
      WorkoutFactory(user=my_user, name="Leg Day")
"""
from datetime import date, time, timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from factory.django import DjangoModelFactory

User = get_user_model()


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    password = "TestPass123!"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Use create_user so the password is properly hashed.
        return model_class.objects.create_user(**kwargs)


# ---------------------------------------------------------------------------
# Exercises
# ---------------------------------------------------------------------------

class ExerciseFactory(DjangoModelFactory):
    class Meta:
        model = "exercises.Exercise"

    name = factory.Sequence(lambda n: f"Exercise {n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
    category = "strength"
    primary_muscle = "chest"
    equipment = "barbell"
    is_compound = False
    met_value = "4.0"


# ---------------------------------------------------------------------------
# Workouts
# ---------------------------------------------------------------------------

class WorkoutFactory(DjangoModelFactory):
    class Meta:
        model = "workouts.Workout"

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Workout {n}")
    started_at = factory.LazyFunction(timezone.now)
    status = "completed"


class RoutineFactory(DjangoModelFactory):
    class Meta:
        model = "workouts.Routine"

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Routine {n}")
    is_public = False


class WorkoutExerciseFactory(DjangoModelFactory):
    class Meta:
        model = "workouts.WorkoutExercise"

    workout = factory.SubFactory(WorkoutFactory)
    exercise = factory.SubFactory(ExerciseFactory)
    order = factory.Sequence(lambda n: n)


class ExerciseSetFactory(DjangoModelFactory):
    class Meta:
        model = "workouts.ExerciseSet"

    workout_exercise = factory.SubFactory(WorkoutExerciseFactory)
    set_number = factory.Sequence(lambda n: n + 1)
    reps = 10
    weight = "60.00"
    completed = True


class RoutineExerciseFactory(DjangoModelFactory):
    class Meta:
        model = "workouts.RoutineExercise"

    routine = factory.SubFactory(RoutineFactory)
    exercise = factory.SubFactory(ExerciseFactory)
    order = factory.Sequence(lambda n: n)
    target_sets = 3
    target_reps = 10
    rest_sec = 60


# ---------------------------------------------------------------------------
# Nutrition
# ---------------------------------------------------------------------------

class FoodFactory(DjangoModelFactory):
    class Meta:
        model = "nutrition.Food"

    name = factory.Sequence(lambda n: f"Food {n}")
    calories = "200.00"
    protein_g = "20.00"
    carbs_g = "25.00"
    fat_g = "5.00"
    fiber_g = "3.00"
    sugar_g = "2.00"
    is_public = True


class MealFactory(DjangoModelFactory):
    class Meta:
        model = "nutrition.Meal"

    user = factory.SubFactory(UserFactory)
    meal_type = "breakfast"
    consumed_at = factory.LazyFunction(timezone.now)


class MealItemFactory(DjangoModelFactory):
    class Meta:
        model = "nutrition.MealItem"

    meal = factory.SubFactory(MealFactory)
    food = factory.SubFactory(FoodFactory)
    servings = "1.00"


class WaterLogFactory(DjangoModelFactory):
    class Meta:
        model = "nutrition.WaterLog"

    user = factory.SubFactory(UserFactory)
    amount_ml = 500
    logged_at = factory.LazyFunction(timezone.now)


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------

class BodyMeasurementFactory(DjangoModelFactory):
    class Meta:
        model = "measurements.BodyMeasurement"

    user = factory.SubFactory(UserFactory)
    # Use a Sequence so multiple measurements for the same user use different dates.
    recorded_at = factory.Sequence(lambda n: date(2024, 1, 1) + timedelta(days=n))
    weight_kg = "75.00"
    body_fat_percent = "20.00"


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

class GoalFactory(DjangoModelFactory):
    class Meta:
        model = "goals.Goal"

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Goal {n}")
    goal_type = "weight_loss"
    target_value = "75.00"
    starting_value = "85.00"
    current_value = "85.00"
    status = "active"


# ---------------------------------------------------------------------------
# Social
# ---------------------------------------------------------------------------

class PostFactory(DjangoModelFactory):
    class Meta:
        model = "social.Post"

    user = factory.SubFactory(UserFactory)
    body = factory.Faker("paragraph", nb_sentences=2)


class FriendshipFactory(DjangoModelFactory):
    class Meta:
        model = "social.Friendship"

    requester = factory.SubFactory(UserFactory)
    addressee = factory.SubFactory(UserFactory)
    status = "accepted"


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = "social.Comment"

    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(UserFactory)
    body = factory.Faker("sentence")


class LikeFactory(DjangoModelFactory):
    class Meta:
        model = "social.Like"

    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(UserFactory)


# ---------------------------------------------------------------------------
# Achievements
# ---------------------------------------------------------------------------

class AchievementFactory(DjangoModelFactory):
    class Meta:
        model = "achievements.Achievement"

    code = factory.Sequence(lambda n: f"achievement-{n}")
    name = factory.Sequence(lambda n: f"Achievement {n}")
    description = "Complete a milestone."
    icon = "trophy"
    kind = "workout_count"
    threshold = 1


class UserAchievementFactory(DjangoModelFactory):
    class Meta:
        model = "achievements.UserAchievement"

    user = factory.SubFactory(UserFactory)
    achievement = factory.SubFactory(AchievementFactory)


class StreakFactory(DjangoModelFactory):
    class Meta:
        model = "achievements.Streak"

    user = factory.SubFactory(UserFactory)
    current_days = 0
    longest_days = 0


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

class ReminderFactory(DjangoModelFactory):
    class Meta:
        model = "reminders.Reminder"

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Reminder {n}")
    reminder_type = "workout"
    time_of_day = time(8, 0)
    days_of_week = []
    is_active = True


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = "notifications.Notification"

    recipient = factory.SubFactory(UserFactory)
    actor = factory.SubFactory(UserFactory)
    notif_type = "like"
    message = factory.Sequence(lambda n: f"Notification {n}")
    target_url = ""
    read = False
