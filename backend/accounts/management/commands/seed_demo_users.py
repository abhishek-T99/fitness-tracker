"""
Management command: seed_demo_users

Creates 15 demo users with realistic data across every domain so the whole
application flow can be explored without manual setup.

Usage:
    python manage.py seed_demo_users          # create / refresh demo data
    python manage.py seed_demo_users --flush  # wipe demo users first, then recreate

All demo accounts share the password:  FitPass123!
"""

import random
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()

PASSWORD = "nepal@123"

# ---------------------------------------------------------------------------
# User roster
# ---------------------------------------------------------------------------
USERS = [
    # username, email, first, last, gender, dob, height_cm, activity, bio, calorie_goal
    ("alice",   "alice@demo.com",   "Alice",   "Chen",     "female", date(1995, 3, 12), 165, "active",    "Powerlifter & coffee addict ☕",          2100),
    ("bob",     "bob@demo.com",     "Bob",     "Smith",    "male",   date(1990, 7, 4),  178, "moderate",  "Gym 3x a week, football weekends 🏈",     2500),
    ("carol",   "carol@demo.com",   "Carol",   "Jones",    "female", date(1998, 11, 22), 162, "light",   "Macro tracking nerd 🥗",                   1800),
    ("dave",    "dave@demo.com",    "Dave",    "Kim",      "male",   date(2000, 1, 30), 175, "sedentary", "Just starting out, wish me luck! 🙏",     2000),
    ("eve",     "eve@demo.com",     "Eve",     "Patel",    "female", date(1993, 5, 17), 170, "athlete",   "Marathon runner. 42km is just a warm-up 🏃", 2400),
    ("frank",   "frank@demo.com",   "Frank",   "Russo",    "male",   date(1988, 9, 3),  182, "active",    "Chasing my 200kg squat PR 🏋️",            3000),
    ("grace",   "grace@demo.com",   "Grace",   "Lin",      "female", date(1997, 2, 14), 158, "moderate",  "Yoga + weights combo 🧘",                 1900),
    ("henry",   "henry@demo.com",   "Henry",   "Park",     "male",   date(1985, 6, 28), 180, "light",     "Tracking everything obsessively 📊",       2200),
    ("iris",    "iris@demo.com",    "Iris",    "Nguyen",   "female", date(1999, 8, 9),  163, "moderate",  "Here for the community 💪",               1950),
    ("jack",    "jack@demo.com",    "Jack",    "Brown",    "male",   date(1992, 12, 1), 176, "active",    "Goal-setter, habit-builder 🎯",           2300),
    ("kate",    "kate@demo.com",    "Kate",    "Wilson",   "female", date(1996, 4, 18), 167, "moderate",  "Reminders keep me on track ⏰",           2000),
    ("liam",    "liam@demo.com",    "Liam",    "Taylor",   "male",   date(1994, 10, 7), 179, "sedentary", "Taking a break from training 😅",         2100),
    ("mia",     "mia@demo.com",     "Mia",     "Davis",    "female", date(2002, 7, 25), 160, "light",     "New here, still figuring things out 👋",  1700),
    ("noah",    "noah@demo.com",    "Noah",    "Martinez", "male",   date(1991, 3, 19), 181, "active",    "CrossFit evangelist 🔥",                  2800),
    ("olivia",  "olivia@demo.com",  "Olivia",  "Anderson", "female", date(1996, 9, 5),  168, "active",    "Hit my goal weight — now maintaining 🎉", 1950),
]


class Command(BaseCommand):
    help = "Seed 15 demo users with data across all app domains."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo users before recreating them.",
        )

    def handle(self, *args, **options):
        self._log("Ensuring exercises, foods, and achievements are seeded…")
        call_command("seed_exercises", verbosity=0)
        call_command("seed_foods", verbosity=0)
        call_command("seed_achievements", verbosity=0)

        if options["flush"]:
            usernames = [u[0] for u in USERS]
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            self._log(f"Flushed {deleted} existing demo user(s).")

        from exercises.models import Exercise
        from nutrition.models import Food

        exercises = list(Exercise.objects.all())
        foods = list(Food.objects.filter(is_public=True))

        if not exercises:
            self.stderr.write("No exercises found — run seed_exercises first.")
            return
        if not foods:
            self.stderr.write("No foods found — run seed_foods first.")
            return

        users = self._create_users()
        self._create_friendships(users)
        self._create_workouts(users, exercises)
        self._create_nutrition(users, foods)
        self._create_measurements(users)
        self._create_goals(users)
        self._create_social(users)
        self._create_achievements(users)
        self._create_reminders(users)

        self._print_credentials()

    # ------------------------------------------------------------------
    # Users & profiles
    # ------------------------------------------------------------------

    def _create_users(self):
        from accounts.models import Profile

        created_users = []
        for (username, email, first, last, gender, dob, height, activity, bio, cal_goal) in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    email=email,
                    first_name=first,
                    last_name=last,
                    is_active=True,
                ),
            )
            if created:
                user.set_password(PASSWORD)
                user.save()

            Profile.objects.update_or_create(
                user=user,
                defaults=dict(
                    bio=bio,
                    date_of_birth=dob,
                    gender=gender,
                    height_cm=height,
                    activity_level=activity,
                    daily_calorie_goal=cal_goal,
                    weekly_workout_goal=random.randint(3, 5),
                    units="metric",
                ),
            )
            created_users.append(user)

        self._log(f"Users ready: {len(created_users)}")
        return created_users

    # ------------------------------------------------------------------
    # Friendships
    # ------------------------------------------------------------------

    def _create_friendships(self, users):
        from social.models import Friendship

        # Accepted pairs — a dense social graph
        accepted_pairs = [
            (0, 1), (0, 2), (0, 4), (0, 5), (0, 8),   # alice is popular
            (1, 2), (1, 5), (1, 9),
            (2, 6), (2, 8),
            (3, 13), (4, 6), (5, 9),
            (7, 10), (8, 9), (8, 14),
            (10, 11), (11, 12),
        ]
        for i, j in accepted_pairs:
            Friendship.objects.get_or_create(
                requester=users[i], addressee=users[j],
                defaults={"status": "accepted"},
            )

        # Pending requests — to test accept/decline flow
        pending_pairs = [
            (13, 0),   # noah → alice (pending)
            (12, 4),   # mia → eve (pending)
            (6, 3),    # grace → dave (pending)
            (14, 7),   # olivia → henry (pending)
        ]
        for i, j in pending_pairs:
            Friendship.objects.get_or_create(
                requester=users[i], addressee=users[j],
                defaults={"status": "pending"},
            )

        self._log("Friendships seeded.")

    # ------------------------------------------------------------------
    # Workouts
    # ------------------------------------------------------------------

    def _create_workouts(self, users, exercises):
        from workouts.models import (
            ExerciseSet,
            Routine,
            RoutineExercise,
            Workout,
            WorkoutExercise,
        )

        today = timezone.now()

        # Workout templates per user archetype: (name, day_offset, exercise_slice, sets_per_ex)
        TEMPLATES = {
            "alice":  [("Push Day", 0, exercises[:3], 4), ("Pull Day", 2, exercises[3:6], 4),
                       ("Leg Day", 4, exercises[6:9], 4), ("Upper Body", 7, exercises[:4], 3),
                       ("Full Body", 9, exercises[5:10], 3)],
            "bob":    [("Chest & Tri", 1, exercises[:2], 3), ("Back & Bi", 3, exercises[2:5], 3),
                       ("Legs", 6, exercises[6:8], 3)],
            "eve":    [("Morning Run", 0, exercises[:1], 1), ("Intervals", 3, exercises[1:2], 1),
                       ("Long Run", 5, exercises[:1], 1), ("Recovery Run", 8, exercises[:1], 1)],
            "frank":  [("Squat Focus", 0, exercises[6:9], 5), ("Bench Focus", 2, exercises[:3], 5),
                       ("Deadlift Day", 4, exercises[3:6], 5), ("Overhead Press", 7, exercises[:2], 4),
                       ("Accessory Work", 9, exercises[9:12], 4)],
            "grace":  [("Yoga Flow", 1, exercises[:1], 2), ("Strength + Yoga", 4, exercises[:3], 2),
                       ("Full Body", 7, exercises[2:5], 3)],
            "jack":   [("HIIT", 0, exercises[:3], 3), ("Strength", 3, exercises[3:6], 4),
                       ("Cardio", 6, exercises[:1], 1)],
            "noah":   [("CrossFit WOD", 0, exercises[:4], 3), ("WOD", 2, exercises[4:7], 3),
                       ("Strength", 5, exercises[7:10], 4), ("Metcon", 8, exercises[:3], 3)],
            "iris":   [("Group Class", 2, exercises[:3], 3), ("Home Workout", 5, exercises[3:5], 3)],
            "olivia": [("Maintenance A", 1, exercises[:4], 3), ("Maintenance B", 4, exercises[4:7], 3)],
            "kate":   [("Morning Workout", 0, exercises[:3], 3), ("Evening Session", 5, exercises[2:5], 3)],
            "dave":   [("First Workout!", 3, exercises[:2], 2)],
            "carol":  [("Light Session", 6, exercises[:2], 2), ("Quick Workout", 13, exercises[2:4], 2)],
        }

        username_to_user = {u.username: u for u in users}

        for username, templates in TEMPLATES.items():
            user = username_to_user.get(username)
            if not user:
                continue

            # Create a routine for power users
            if username in ("alice", "frank", "noah"):
                routine, _ = Routine.objects.get_or_create(
                    user=user, name=f"{user.first_name}'s Main Routine",
                    defaults={
                        "description": "Auto-generated demo routine",
                        "estimated_duration_min": 60,
                    },
                )
                routine.items.all().delete()
                for idx, ex in enumerate(exercises[:4]):
                    RoutineExercise.objects.create(
                        routine=routine, exercise=ex, order=idx,
                        target_sets=4, target_reps=8, rest_sec=90,
                    )

            for name, day_offset, ex_list, n_sets in templates:
                started = today - timedelta(days=day_offset)
                workout = Workout.objects.create(
                    user=user,
                    name=name,
                    started_at=started,
                    ended_at=started + timedelta(minutes=random.randint(45, 90)),
                    duration_min=random.randint(45, 90),
                    calories_burned=random.randint(300, 700),
                    perceived_exertion=random.randint(6, 9),
                    status="completed",
                )
                for ex_order, exercise in enumerate(ex_list[:4]):
                    we = WorkoutExercise.objects.create(
                        workout=workout, exercise=exercise, order=ex_order
                    )
                    base_weight = random.uniform(40, 120)
                    for s in range(1, n_sets + 1):
                        ExerciseSet.objects.create(
                            workout_exercise=we,
                            set_number=s,
                            reps=random.randint(5, 12),
                            weight=round(base_weight + (s - 1) * 2.5, 2),
                            rpe=random.randint(7, 9),
                            completed=True,
                        )

        self._log("Workouts seeded.")

    # ------------------------------------------------------------------
    # Nutrition
    # ------------------------------------------------------------------

    def _create_nutrition(self, users, foods):
        from nutrition.models import Meal, MealItem, WaterLog

        today = timezone.now()
        meal_plans = {
            "alice":  {"days": 14, "meals_per_day": 4, "water_ml": 2500},
            "bob":    {"days": 7,  "meals_per_day": 3, "water_ml": 2000},
            "carol":  {"days": 30, "meals_per_day": 4, "water_ml": 2200},
            "dave":   {"days": 3,  "meals_per_day": 2, "water_ml": 1500},
            "eve":    {"days": 14, "meals_per_day": 3, "water_ml": 3000},
            "frank":  {"days": 14, "meals_per_day": 5, "water_ml": 3500},
            "grace":  {"days": 7,  "meals_per_day": 3, "water_ml": 2000},
            "jack":   {"days": 10, "meals_per_day": 3, "water_ml": 2500},
            "kate":   {"days": 7,  "meals_per_day": 3, "water_ml": 2000},
            "olivia": {"days": 7,  "meals_per_day": 3, "water_ml": 1800},
        }
        meal_types = ["breakfast", "lunch", "dinner", "snack"]
        meal_hours = {"breakfast": 7, "lunch": 12, "dinner": 19, "snack": 16}

        username_to_user = {u.username: u for u in users}

        for username, plan in meal_plans.items():
            user = username_to_user.get(username)
            if not user:
                continue

            for day in range(plan["days"]):
                dt = today - timedelta(days=day)
                types_today = meal_types[: plan["meals_per_day"]]
                for mtype in types_today:
                    consumed = dt.replace(
                        hour=meal_hours[mtype], minute=0, second=0, microsecond=0
                    )
                    meal = Meal.objects.create(user=user, meal_type=mtype, consumed_at=consumed)
                    for food in random.sample(foods, min(3, len(foods))):
                        MealItem.objects.create(
                            meal=meal,
                            food=food,
                            servings=round(random.uniform(0.5, 2.5), 2),
                        )

                WaterLog.objects.create(
                    user=user,
                    amount_ml=plan["water_ml"] + random.randint(-300, 300),
                    logged_at=dt.replace(hour=20, minute=0, second=0, microsecond=0),
                )

        self._log("Nutrition seeded.")

    # ------------------------------------------------------------------
    # Body measurements
    # ------------------------------------------------------------------

    def _create_measurements(self, users):
        from measurements.models import BodyMeasurement

        today = date.today()
        measurement_data = {
            "alice":  {"weeks": 12, "start_weight": 68.0, "delta": -0.3},
            "bob":    {"weeks": 8,  "start_weight": 85.0, "delta": -0.2},
            "carol":  {"weeks": 16, "start_weight": 62.0, "delta": -0.1},
            "frank":  {"weeks": 12, "start_weight": 95.0, "delta": 0.2},
            "eve":    {"weeks": 10, "start_weight": 60.0, "delta": -0.2},
            "grace":  {"weeks": 6,  "start_weight": 58.0, "delta": -0.1},
            "henry":  {"weeks": 20, "start_weight": 82.0, "delta": -0.15},
            "jack":   {"weeks": 8,  "start_weight": 78.0, "delta": -0.2},
            "olivia": {"weeks": 24, "start_weight": 72.0, "delta": -0.4},
        }
        username_to_user = {u.username: u for u in users}

        for username, cfg in measurement_data.items():
            user = username_to_user.get(username)
            if not user:
                continue

            for week in range(cfg["weeks"]):
                record_date = today - timedelta(weeks=week)
                weight = round(cfg["start_weight"] + cfg["delta"] * week * 7, 2)
                BodyMeasurement.objects.get_or_create(
                    user=user,
                    recorded_at=record_date,
                    defaults=dict(
                        weight_kg=weight,
                        body_fat_percent=round(random.uniform(12, 25), 1),
                        waist_cm=round(random.uniform(70, 90), 1),
                        chest_cm=round(random.uniform(90, 105), 1),
                        resting_hr_bpm=random.randint(52, 72),
                    ),
                )

        self._log("Measurements seeded.")

    # ------------------------------------------------------------------
    # Goals
    # ------------------------------------------------------------------

    def _create_goals(self, users):
        from goals.models import Goal

        today = date.today()
        goal_sets = {
            "alice": [
                ("Bench 80kg",      "strength",        80,  65,  65,  "kg",  today + timedelta(days=90)),
                ("Lose 3kg",        "weight_loss",     65,  68,  67.5,"kg",  today + timedelta(days=60)),
                ("4 workouts/week", "workouts_per_week", 4, 0,   3,   "wkt/wk", None),
            ],
            "bob": [
                ("Drop to 80kg",    "weight_loss",     80,  85,  83,  "kg",  today + timedelta(days=45)),
                ("Run 5km",         "endurance",       5,   0,   3,   "km",  today + timedelta(days=30)),
            ],
            "carol": [
                ("Hit 1800 kcal/day","calories",       1800,0,  1650,"kcal", None),
                ("Lose 5kg",        "weight_loss",     57,  62,  60.5,"kg",  today + timedelta(days=120)),
            ],
            "dave": [
                ("Work out 3x/week","workouts_per_week",3,  0,   1,   "wkt/wk", today + timedelta(days=30)),
            ],
            "frank": [
                ("Squat 180kg PR",  "strength",        180, 140, 160, "kg",  today + timedelta(days=180)),
                ("Gain 5kg muscle", "weight_gain",     100, 95,  97,  "kg",  today + timedelta(days=120)),
                ("3000 kcal/day",   "calories",        3000,0,  2800,"kcal", None),
            ],
            "jack": [
                ("Lose 8kg",        "weight_loss",     70,  78,  74,  "kg",  today + timedelta(days=90)),
                ("5 workouts/week", "workouts_per_week",5,  0,   3,   "wkt/wk", today + timedelta(days=60)),
            ],
            "olivia": [
                ("Maintain 65kg",   "weight_loss",     65,  72,  65,  "kg",  None),     # achieved
                ("10k sub-50min",   "endurance",       50,  65,  49,  "min", today - timedelta(days=10)),  # achieved
            ],
            "eve": [
                ("Sub-4h marathon", "endurance",       240, 280, 255, "min", today + timedelta(days=90)),
                ("Run 50km/week",   "endurance",       50,  0,   38,  "km",  None),
            ],
            "mia": [
                ("Try the gym",     "custom",          1,   0,   0,   "visit", today + timedelta(days=14)),
            ],
        }

        username_to_user = {u.username: u for u in users}

        for username, goals in goal_sets.items():
            user = username_to_user.get(username)
            if not user:
                continue
            for title, gtype, target, start, current, unit, deadline in goals:
                # Determine status from current vs target (for weight_loss: current <= target means achieved)
                if gtype == "weight_loss":
                    status = "achieved" if current <= target else "active"
                else:
                    status = "achieved" if current >= target else "active"

                Goal.objects.get_or_create(
                    user=user, title=title,
                    defaults=dict(
                        goal_type=gtype,
                        target_value=target,
                        starting_value=start,
                        current_value=current,
                        unit=unit,
                        deadline=deadline,
                        status=status,
                    ),
                )

        self._log("Goals seeded.")

    # ------------------------------------------------------------------
    # Social — posts, likes, comments
    # ------------------------------------------------------------------

    def _create_social(self, users):
        from social.models import Comment, Friendship, Like, Post

        post_bodies = {
            "alice":  ["Just hit a new squat PR — 120kg! 🎉",
                       "Rest day today. Meal prepped for the whole week 🥗",
                       "Push day done. Bench is moving up nicely 💪"],
            "bob":    ["Chest day with the boys. Good session!",
                       "Football match today — counts as cardio right? 😅"],
            "eve":    ["10km done before sunrise. Best way to start the day 🌅",
                       "Long run Saturday — 28km in the books. Legs are toast 🏃"],
            "frank":  ["200kg deadlift is COMING. Hit 185kg today 🏋️",
                       "Heavy squat session. Back feels solid."],
            "noah":   ["WOD today: 21-15-9 thrusters + pull-ups. Died. 💀",
                       "CrossFit open prep is going well 🔥"],
            "grace":  ["Morning yoga + afternoon weights. Feeling balanced 🧘"],
            "iris":   ["Love this community! Keep pushing everyone 💙",
                       "Group class was brutal today 😤"],
            "jack":   ["Down 4kg since January. Slow and steady 🎯",
                       "Meal prep Sunday done. Discipline > motivation."],
            "carol":  ["Hit my protein goal every day this week! 💚",
                       "Trying a new food tracking approach this month 📱"],
            "olivia": ["Reached goal weight! Time to focus on maintenance 🎉",
                       "Feeling the best I have in years 🌟"],
        }

        username_to_user = {u.username: u for u in users}
        all_posts = []

        for username, bodies in post_bodies.items():
            user = username_to_user.get(username)
            if not user:
                continue
            for body in bodies:
                post = Post.objects.create(user=user, body=body)
                all_posts.append(post)

        # Likes: friends like each other's posts
        accepted = Friendship.objects.filter(status="accepted").select_related("requester", "addressee")
        for friendship in accepted:
            # requester likes addressee's recent posts and vice versa
            for post in Post.objects.filter(user=friendship.addressee)[:2]:
                Like.objects.get_or_create(post=post, user=friendship.requester)
            for post in Post.objects.filter(user=friendship.requester)[:1]:
                Like.objects.get_or_create(post=post, user=friendship.addressee)

        # Comments
        comment_pairs = [
            ("bob",    "alice",  "Crushing it as always! 🙌"),
            ("alice",  "frank",  "Beast mode activated 🔥"),
            ("iris",   "alice",  "So inspiring!"),
            ("carol",  "olivia", "You did it!! 🎉🎉"),
            ("eve",    "noah",   "CrossFit and running — respect 💪"),
            ("jack",   "carol",  "Macro tracking changed my life too!"),
            ("grace",  "iris",   "Group classes are the best motivation!"),
            ("noah",   "frank",  "Those numbers are insane 😤"),
            ("olivia", "eve",    "Sub-4h is coming for you! 🏃"),
            ("alice",  "jack",   "4kg is huge progress, keep going!"),
        ]
        for commenter_username, post_owner_username, body in comment_pairs:
            commenter = username_to_user.get(commenter_username)
            post_owner = username_to_user.get(post_owner_username)
            if not commenter or not post_owner:
                continue
            post = Post.objects.filter(user=post_owner).first()
            if post:
                Comment.objects.create(post=post, user=commenter, body=body)

        self._log("Social posts, likes, and comments seeded.")

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------

    def _create_achievements(self, users):
        from achievements.models import Achievement, Streak, UserAchievement

        username_to_user = {u.username: u for u in users}

        # Streak data
        streak_data = {
            "alice":  (21, 45),
            "frank":  (14, 30),
            "eve":    (30, 60),
            "noah":   (7,  20),
            "jack":   (5,  14),
            "carol":  (3,  10),
            "olivia": (10, 90),
            "liam":   (0,  15),   # streak decayed
        }
        for username, (current, longest) in streak_data.items():
            user = username_to_user.get(username)
            if not user:
                continue
            last_date = date.today() if current > 0 else date.today() - timedelta(days=5)
            Streak.objects.update_or_create(
                user=user,
                defaults={"current_days": current, "longest_days": longest, "last_workout_date": last_date},
            )

        # Unlock achievements for power users
        all_achievements = list(Achievement.objects.all())
        if not all_achievements:
            return

        unlock_map = {
            "alice":  all_achievements[:3],
            "frank":  all_achievements[:4],
            "eve":    all_achievements[:2],
            "olivia": all_achievements[:5],
            "noah":   all_achievements[:2],
        }
        for username, achievements in unlock_map.items():
            user = username_to_user.get(username)
            if not user:
                continue
            for ach in achievements:
                UserAchievement.objects.get_or_create(user=user, achievement=ach)

        self._log("Achievements and streaks seeded.")

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------

    def _create_reminders(self, users):
        from reminders.models import Reminder

        reminder_sets = {
            "alice": [
                ("Morning Workout", "workout", time(6, 30),  ["mon", "wed", "fri", "sat"]),
                ("Protein Shake",   "meal",    time(8, 0),   ["mon", "tue", "wed", "thu", "fri"]),
                ("Hydration Check", "water",   time(12, 0),  ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
            ],
            "bob": [
                ("Gym Time",        "workout", time(18, 30), ["mon", "wed", "fri"]),
                ("Drink Water",     "water",   time(9, 0),   ["mon", "tue", "wed", "thu", "fri"]),
            ],
            "carol": [
                ("Log Breakfast",   "meal",    time(7, 30),  ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
                ("Log Lunch",       "meal",    time(12, 30), ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
                ("Log Dinner",      "meal",    time(19, 30), ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
            ],
            "dave": [
                ("Beginner Workout","workout", time(19, 0),  ["tue", "thu", "sat"]),
            ],
            "eve": [
                ("Morning Run",     "workout", time(5, 45),  ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
                ("Post-Run Snack",  "meal",    time(7, 0),   ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
            ],
            "frank": [
                ("Heavy Lifting",   "workout", time(7, 0),   ["mon", "wed", "fri"]),
                ("Pre-Workout Meal","meal",    time(6, 30),  ["mon", "wed", "fri"]),
                ("Weigh In",        "measurement", time(7, 15), ["mon"]),
            ],
            "henry": [
                ("Weekly Weigh-In", "measurement", time(8, 0), ["mon"]),
                ("Monthly Measurements", "measurement", time(8, 0), ["mon"]),
            ],
            "kate": [
                ("Morning Workout", "workout", time(7, 0),   ["mon", "tue", "wed", "thu", "fri"]),
                ("Water Reminder",  "water",   time(10, 0),  ["mon", "tue", "wed", "thu", "fri"]),
                ("Water Reminder",  "water",   time(14, 0),  ["mon", "tue", "wed", "thu", "fri"]),
                ("Evening Walk",    "workout", time(19, 30), ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
            ],
            "jack": [
                ("Morning Weigh-In","measurement", time(7, 0), ["mon", "wed", "fri"]),
                ("Workout Time",    "workout", time(17, 30), ["mon", "tue", "wed", "thu", "fri"]),
            ],
        }
        username_to_user = {u.username: u for u in users}

        for username, reminders in reminder_sets.items():
            user = username_to_user.get(username)
            if not user:
                continue
            for title, rtype, tod, days in reminders:
                Reminder.objects.get_or_create(
                    user=user, title=title, time_of_day=tod,
                    defaults={"reminder_type": rtype, "days_of_week": days, "is_active": True},
                )

        self._log("Reminders seeded.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log(self, msg):
        self.stdout.write(f"  {msg}")

    def _print_credentials(self):
        self.stdout.write("\n" + self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  Demo users created — all share password: FitPass123!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        rows = [
            ("Username", "Name",          "Archetype"),
            ("--------", "----",          "---------"),
            ("alice",    "Alice Chen",    "Power lifter, active social"),
            ("bob",      "Bob Smith",     "Moderate gym-goer"),
            ("carol",    "Carol Jones",   "Nutrition tracker"),
            ("dave",     "Dave Kim",      "Beginner (minimal data)"),
            ("eve",      "Eve Patel",     "Endurance runner"),
            ("frank",    "Frank Russo",   "Strength athlete"),
            ("grace",    "Grace Lin",     "Yoga + weights"),
            ("henry",    "Henry Park",    "Measurement obsessive"),
            ("iris",     "Iris Nguyen",   "Social / community"),
            ("jack",     "Jack Brown",    "Goal-oriented, cutting"),
            ("kate",     "Kate Wilson",   "Reminder-heavy user"),
            ("liam",     "Liam Taylor",   "Inactive (streak decayed)"),
            ("mia",      "Mia Davis",     "New user (sparse data)"),
            ("noah",     "Noah Martinez", "CrossFit, pending requests"),
            ("olivia",   "Olivia Anderson","Goals achieved, maintaining"),
        ]
        for username, name, archetype in rows:
            self.stdout.write(f"  {username:<10} {name:<20} {archetype}")
        self.stdout.write(self.style.SUCCESS("=" * 60) + "\n")
