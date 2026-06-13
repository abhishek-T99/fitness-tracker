"""
Management command: seed_demo_users

Creates 5 demo users with deeply realistic data — workouts spread over months,
progressive overload, weight-loss and muscle-gain trajectories, daily nutrition
logs, and an active social graph with posts, likes and comments.

Usage:
    python manage.py seed_demo_users           # create / refresh
    python manage.py seed_demo_users --flush   # wipe first, then recreate

All accounts share the password:  nepal@123

Personas
--------
alice   Alice Chen     Powerlifter, 6-month cut, very social, 24 weeks of data
marcus  Marcus Webb    Marathon runner, Boston qualifier training, 16 weeks
sofia   Sofia Rodriguez Weight-loss journey, -8 kg so far, nutrition obsessive, 20 weeks
jake    Jake Turner    Beginner, 2 months in, inconsistent but improving, 8 weeks
priya   Priya Kapoor   CrossFit athlete, 8 months, most data, most achievements
"""

import random
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()
PASSWORD = "nepal@123"

# ── Persona definitions ───────────────────────────────────────────────────────
# (username, email, first, last, gender, dob, height_cm, activity, bio, cal_goal)
PERSONAS = [
    ("alice",  "alice@demo.com",  "Alice",  "Chen",      "female", date(1996,  3, 12), 165, "active",   "Powerlifter & coffee addict ☕ | Chasing that 100kg bench", 2200),
    ("marcus", "marcus@demo.com", "Marcus", "Webb",      "male",   date(1990,  7, 20), 178, "athlete",  "Boston qualifier or bust 🏃 | Sub-3:45 is the goal",       2800),
    ("sofia",  "sofia@demo.com",  "Sofia",  "Rodriguez", "female", date(1993,  5,  8), 163, "moderate", "Down 8 kg and counting 💚 | Macros tracked daily",          1750),
    ("jake",   "jake@demo.com",   "Jake",   "Turner",    "male",   date(2002, 11, 14), 176, "light",    "2 months in. Still figuring things out 👋",                 2400),
    ("priya",  "priya@demo.com",  "Priya",  "Kapoor",    "female", date(1995,  9,  3), 160, "athlete",  "CrossFit | 8 months strong | Community > everything 🔥",    2100),
]

# ── Exercise name → object cache (populated in handle()) ─────────────────────
EX: dict = {}


def ex(*names):
    """Return a list of Exercise objects by name (silently skips missing)."""
    return [EX[n] for n in names if n in EX]


# ── Workout session blueprints ─────────────────────────────────────────────────
#
# Each entry: (session_name, hour, duration_min, base_calories, exercise_names, sets, reps,
#              base_weights_today_kg)
# base_weights_today_kg align 1:1 with exercise_names for strength sessions.
# Runners use distance_km instead (sets=1, reps=0, weight=0).

ALICE_SESSIONS = [
    ("Push Day",   7, 70, 520, ["Bench Press","Incline Dumbbell Press","Overhead Press","Lateral Raise","Tricep Pushdown"], 4, [8,10,8,12,12], [87.5,52.5,55,12.5,35]),
    ("Pull Day",   7, 65, 490, ["Bent-Over Row","Lat Pulldown","Seated Cable Row","Barbell Curl","Face Pull"],              4, [8,10,10,10,15], [72.5,65,55,32.5,20]),
    ("Leg Day",    8, 80, 620, ["Back Squat","Romanian Deadlift","Leg Press","Walking Lunge","Calf Raise"],                 5, [6,8,10,12,15],  [112.5,72.5,120,20,60]),
    ("Upper Body", 7, 60, 460, ["Bench Press","Bent-Over Row","Overhead Press","Pull-up","Lateral Raise"],                 3, [8,8,8,6,12],    [85,70,52.5,0,12.5]),
]
# Alice trains Mon=Push, Wed=Pull, Thu=Legs, Sat=Upper
ALICE_SCHED = [(0,"Push Day"),(2,"Pull Day"),(3,"Leg Day"),(5,"Upper Body")]  # day offset 0=Mon

MARCUS_RUNS = [
    # (name, day_offset, hour, distance_km, duration_min, calories)
    ("Easy Run",    0, 6, 9.0,  52, 480),
    ("Easy Run",    1, 6, 8.5,  49, 450),
    ("Speed Work",  2, 6, 11.0, 55, 580),
    ("Easy Run",    3, 6, 9.0,  52, 480),
    ("Easy Run",    4, 6, 8.5,  49, 450),
    ("Long Run",    5, 6, None, None, None),  # distance/duration varies by week
]

SOFIA_SESSIONS = [
    ("Cardio + Core",    7, 55, 380, ["Running","Plank","Hanging Leg Raise","Burpees"],                              3, [0,45,12,15], [0,0,0,0]),
    ("Full Body Lift",   8, 60, 350, ["Back Squat","Bench Press","Bent-Over Row","Overhead Press","Walking Lunge"],  3, [10,10,10,10,12], [45,35,30,25,15]),
    ("HIIT + Strength",  7, 50, 360, ["Burpees","Jump Rope","Leg Press","Lat Pulldown","Plank"],                    3, [0,0,12,12,45],  [0,0,50,42.5,0]),
]
SOFIA_SCHED = [(0,"Cardio + Core"),(2,"Full Body Lift"),(4,"HIIT + Strength")]

JAKE_SESSIONS = [
    ("Full Body A", 18, 50, 300, ["Back Squat","Bench Press","Bent-Over Row","Overhead Press"],   3, [8,8,8,8], [50,45,35,25]),
    ("Full Body B", 18, 45, 280, ["Deadlift","Push-up","Lat Pulldown","Walking Lunge","Plank"],   3, [6,10,10,10,30],[70,0,40,12.5,0]),
]
JAKE_SCHED = [(0,"Full Body A"),(2,"Full Body B")]  # Mon+Wed, sometimes Fri

PRIYA_SESSIONS = [
    ("WOD A",        6, 65, 560, ["Burpees","Pull-up","Back Squat","Overhead Press","Plank"],       4, [15,10,10,8,45],  [0,0,60,35,0]),
    ("WOD B",        6, 60, 530, ["Deadlift","Bench Press","Bent-Over Row","Jump Rope","Push-up"],  4, [8,10,10,0,20],   [80,57.5,52.5,0,0]),
    ("Strength",     7, 70, 510, ["Back Squat","Deadlift","Overhead Press","Pull-up","Barbell Curl"],4,[6,5,8,8,10],    [72.5,95,42.5,0,27.5]),
    ("Metcon",       6, 55, 540, ["Burpees","Jump Rope","Hanging Leg Raise","Bent-Over Row","Plank"],3,[20,0,15,10,60],[0,0,0,50,0]),
    ("Open Prep",    6, 75, 580, ["Back Squat","Bench Press","Pull-up","Deadlift","Burpees"],       4, [8,8,10,6,15],   [67.5,55,0,87.5,0]),
]
PRIYA_SCHED = [(0,"WOD A"),(1,"WOD B"),(3,"Strength"),(4,"Metcon"),(5,"Open Prep")]


# ── Meal templates (realistic eating patterns per persona) ────────────────────
# Foods listed as (name, servings_range)
ALICE_MEALS = {
    "breakfast": [("Oats (dry)",1.5),("Whey Protein Powder",1),("Banana",1)],
    "lunch":     [("Chicken Breast (cooked)",1.5),("Brown Rice (cooked)",2),("Broccoli (cooked)",2)],
    "dinner":    [("Salmon (cooked)",1.2),("Sweet Potato (baked)",2),("Broccoli (cooked)",1.5)],
    "snack":     [("Greek Yogurt (plain, non-fat)",1),("Almonds",0.5),("Apple",1)],
}
MARCUS_MEALS = {
    "breakfast": [("Oats (dry)",2),("Banana",2),("Whole Milk",1.5)],
    "lunch":     [("Whole Wheat Bread",3),("Chicken Breast (cooked)",1.5),("Avocado",0.5)],
    "dinner":    [("White Rice (cooked)",3),("Ground Beef 90/10 (cooked)",1.2),("Broccoli (cooked)",1.5)],
    "snack":     [("Banana",1),("Peanut Butter",1),("Whey Protein Powder",1)],
}
SOFIA_MEALS = {
    "breakfast": [("Egg, large",2),("Oats (dry)",1),("Apple",1)],
    "lunch":     [("Chicken Breast (cooked)",1),("Brown Rice (cooked)",1),("Broccoli (cooked)",2)],
    "dinner":    [("Tofu (firm)",1.5),("Lentils (cooked)",1.5),("Broccoli (cooked)",2)],
    "snack":     [("Greek Yogurt (plain, non-fat)",1),("Apple",1)],
}
JAKE_MEALS = {
    "breakfast": [("Egg, large",3),("Whole Wheat Bread",2),("Whole Milk",1)],
    "lunch":     [("Ground Beef 90/10 (cooked)",1.2),("White Rice (cooked)",2.5)],
    "dinner":    [("Chicken Breast (cooked)",1.2),("White Rice (cooked)",2),("Broccoli (cooked)",1)],
}
PRIYA_MEALS = {
    "breakfast": [("Greek Yogurt (plain, non-fat)",1.5),("Oats (dry)",1),("Banana",1),("Whey Protein Powder",1)],
    "lunch":     [("Chicken Breast (cooked)",2),("Sweet Potato (baked)",2),("Avocado",0.5)],
    "dinner":    [("Salmon (cooked)",1.2),("Brown Rice (cooked)",1.5),("Broccoli (cooked)",2)],
    "snack":     [("Almonds",0.5),("Whey Protein Powder",1),("Apple",1)],
}


class Command(BaseCommand):
    help = "Seed 5 realistic demo users with months of activity data."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true",
                            help="Delete existing demo users before recreating.")

    def handle(self, *args, **options):
        self._log("Ensuring exercises, foods, and achievements are seeded…")
        call_command("seed_exercises", verbosity=0)
        call_command("seed_foods", verbosity=0)
        call_command("seed_achievements", verbosity=0)

        if options["flush"]:
            usernames = [p[0] for p in PERSONAS]
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            self._log(f"Flushed {deleted} existing demo user(s).")

        # Populate the exercise cache by name
        from exercises.models import Exercise
        for e in Exercise.objects.all():
            EX[e.name] = e

        from nutrition.models import Food
        food_map = {f.name: f for f in Food.objects.filter(is_public=True)}

        users_by_name = {}
        for row in PERSONAS:
            u = self._create_user(*row)
            users_by_name[u.username] = u

        self._create_friendships(users_by_name)
        self._create_workouts(users_by_name)
        self._create_measurements(users_by_name)
        self._create_nutrition(users_by_name, food_map)
        self._create_goals(users_by_name)
        self._create_social(users_by_name)
        self._create_achievements(users_by_name)
        self._create_reminders(users_by_name)
        self._print_credentials()

    # ── Users & profiles ──────────────────────────────────────────────────────

    def _create_user(self, username, email, first, last, gender, dob, height, activity, bio, cal_goal):
        from accounts.models import Profile
        user, created = User.objects.get_or_create(
            username=username,
            defaults=dict(email=email, first_name=first, last_name=last, is_active=True),
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
        Profile.objects.update_or_create(
            user=user,
            defaults=dict(bio=bio, date_of_birth=dob, gender=gender, height_cm=height,
                          activity_level=activity, daily_calorie_goal=cal_goal,
                          weekly_workout_goal=5 if activity == "athlete" else 3,
                          units="metric"),
        )
        return user

    # ── Friendships ───────────────────────────────────────────────────────────

    def _create_friendships(self, u):
        from social.models import Friendship
        # All five are mutually connected (accepted)
        names = list(u.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                Friendship.objects.get_or_create(
                    requester=u[names[i]], addressee=u[names[j]],
                    defaults={"status": "accepted"},
                )
        self._log("Friendships: all 5 users connected.")

    # ── Workouts ──────────────────────────────────────────────────────────────

    def _create_workouts(self, u):
        from workouts.models import Workout, WorkoutExercise, ExerciseSet, Routine, RoutineExercise

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # ── Alice ─────────────────────────────────────────────────────────────
        alice = u["alice"]
        routine, _ = Routine.objects.get_or_create(
            user=alice, name="Powerlifting 4-Day Split",
            defaults={"description": "Push/Pull/Legs/Upper. Progressive overload every session.",
                      "estimated_duration_min": 70},
        )
        routine.items.all().delete()
        for idx, nm in enumerate(["Bench Press","Back Squat","Deadlift","Bent-Over Row"]):
            if nm in EX:
                RoutineExercise.objects.create(routine=routine, exercise=EX[nm], order=idx,
                                               target_sets=4, target_reps=8, rest_sec=180)
        total_weeks = 24
        for week in range(total_weeks):
            pf = 1 - (week / total_weeks) * 0.22  # progression factor: 1.0 today → 0.78 oldest
            for day_offset, sname in ALICE_SCHED:
                if _skip("alice", week, day_offset, 8): continue
                tmpl = next(s for s in ALICE_SESSIONS if s[0] == sname)
                _, hour, dur, cal, exnames, sets, reps_list, weights = tmpl
                dt = today - timedelta(weeks=week, days=day_offset)
                dt = dt.replace(hour=hour)
                w = Workout.objects.create(
                    user=alice, name=sname,
                    started_at=dt, ended_at=dt + timedelta(minutes=dur),
                    duration_min=dur,
                    calories_burned=_jitter(cal, 50),
                    perceived_exertion=random.randint(7, 9),
                    status="completed",
                )
                for oi, (ename, n_sets, reps, wt_today) in enumerate(
                        zip(exnames, [sets]*len(exnames), reps_list, weights)):
                    if ename not in EX:
                        continue
                    we = WorkoutExercise.objects.create(workout=w, exercise=EX[ename], order=oi)
                    for s in range(1, n_sets + 1):
                        actual_wt = round_weight(wt_today * pf * (1 + (s-1)*0.025)) if wt_today else None
                        ExerciseSet.objects.create(
                            workout_exercise=we, set_number=s,
                            reps=reps if reps else None,
                            weight=actual_wt,
                            duration_sec=reps if not wt_today and reps > 20 else None,
                            rpe=random.randint(7, 9), completed=True,
                        )

        # ── Marcus ────────────────────────────────────────────────────────────
        marcus = u["marcus"]
        total_weeks = 16
        for week in range(total_weeks):
            pf = 1 - (week / total_weeks) * 0.15  # pace/distance improves over time
            for run in MARCUS_RUNS:
                name, day_off, hour, dist, dur, cal = run
                if _skip("marcus", week, day_off, 6): continue
                dt = (today - timedelta(weeks=week, days=day_off)).replace(hour=hour)

                # Long run: scale with week progression
                if name == "Long Run":
                    dist = round(18 + (total_weeks - week) * 0.7, 1)  # 18→29 km progression
                    dur  = int(dist * 5.5)   # ~5:30/km easy long-run pace
                    cal  = int(dist * 65)
                else:
                    dist = round(dist * pf, 1)
                    dur  = dur or int(dist * 5.2)
                    cal  = cal or int(dist * 60)

                w = Workout.objects.create(
                    user=marcus, name=name,
                    started_at=dt, ended_at=dt + timedelta(minutes=dur),
                    duration_min=dur, distance_km=dist,
                    calories_burned=_jitter(cal, 40),
                    perceived_exertion=random.randint(6, 8),
                    status="completed",
                )
                if "Running" in EX:
                    we = WorkoutExercise.objects.create(workout=w, exercise=EX["Running"], order=0)
                    ExerciseSet.objects.create(
                        workout_exercise=we, set_number=1,
                        distance_m=int(dist * 1000), duration_sec=dur * 60, completed=True,
                    )

        # ── Sofia ─────────────────────────────────────────────────────────────
        sofia = u["sofia"]
        total_weeks = 20
        for week in range(total_weeks):
            pf = 1 - (week / total_weeks) * 0.28
            for day_offset, sname in SOFIA_SCHED:
                if _skip("sofia", week, day_offset, 12): continue
                tmpl = next(s for s in SOFIA_SESSIONS if s[0] == sname)
                _, hour, dur, cal, exnames, sets, reps_list, weights = tmpl
                dt = (today - timedelta(weeks=week, days=day_offset)).replace(hour=hour)
                w = Workout.objects.create(
                    user=sofia, name=sname,
                    started_at=dt, ended_at=dt + timedelta(minutes=dur),
                    duration_min=dur, calories_burned=_jitter(cal, 40),
                    perceived_exertion=random.randint(6, 8), status="completed",
                )
                for oi, (ename, n_sets, reps, wt_today) in enumerate(
                        zip(exnames, [sets]*len(exnames), reps_list, weights)):
                    if ename not in EX: continue
                    we = WorkoutExercise.objects.create(workout=w, exercise=EX[ename], order=oi)
                    for s in range(1, n_sets + 1):
                        actual_wt = round_weight(wt_today * pf) if wt_today else None
                        ExerciseSet.objects.create(
                            workout_exercise=we, set_number=s,
                            reps=reps if reps else None,
                            weight=actual_wt,
                            duration_sec=reps if not wt_today and reps > 20 else None,
                            rpe=random.randint(6, 8), completed=True,
                        )

        # ── Jake ─────────────────────────────────────────────────────────────
        jake = u["jake"]
        total_weeks = 8
        for week in range(total_weeks):
            pf = 1 - (week / total_weeks) * 0.30
            for day_offset, sname in JAKE_SCHED:
                # Jake is inconsistent — higher skip rate + sometimes adds Friday
                if _skip("jake", week, day_offset, 25): continue
                tmpl = next(s for s in JAKE_SESSIONS if s[0] == sname)
                _, hour, dur, cal, exnames, sets, reps_list, weights = tmpl
                dt = (today - timedelta(weeks=week, days=day_offset)).replace(hour=hour)
                w = Workout.objects.create(
                    user=jake, name=sname,
                    started_at=dt, ended_at=dt + timedelta(minutes=dur),
                    duration_min=dur, calories_burned=_jitter(cal, 40),
                    perceived_exertion=random.randint(6, 9), status="completed",
                )
                for oi, (ename, n_sets, reps, wt_today) in enumerate(
                        zip(exnames, [sets]*len(exnames), reps_list, weights)):
                    if ename not in EX: continue
                    we = WorkoutExercise.objects.create(workout=w, exercise=EX[ename], order=oi)
                    for s in range(1, n_sets + 1):
                        actual_wt = round_weight(wt_today * pf) if wt_today else None
                        ExerciseSet.objects.create(
                            workout_exercise=we, set_number=s,
                            reps=reps if reps else None,
                            weight=actual_wt,
                            rpe=random.randint(6, 9), completed=True,
                        )

        # ── Priya ─────────────────────────────────────────────────────────────
        priya = u["priya"]
        routine2, _ = Routine.objects.get_or_create(
            user=priya, name="CrossFit 5-Day Program",
            defaults={"description": "5 days a week. Strength + Metcons. No excuses.",
                      "estimated_duration_min": 65},
        )
        routine2.items.all().delete()
        for idx, nm in enumerate(["Back Squat","Deadlift","Pull-up","Overhead Press"]):
            if nm in EX:
                RoutineExercise.objects.create(routine=routine2, exercise=EX[nm], order=idx,
                                               target_sets=4, target_reps=8, rest_sec=120)
        total_weeks = 32
        for week in range(total_weeks):
            pf = 1 - (week / total_weeks) * 0.25
            for day_offset, sname in PRIYA_SCHED:
                if _skip("priya", week, day_offset, 8): continue
                tmpl = next(s for s in PRIYA_SESSIONS if s[0] == sname)
                _, hour, dur, cal, exnames, sets, reps_list, weights = tmpl
                dt = (today - timedelta(weeks=week, days=day_offset)).replace(hour=hour)
                w = Workout.objects.create(
                    user=priya, name=sname,
                    started_at=dt, ended_at=dt + timedelta(minutes=dur),
                    duration_min=dur, calories_burned=_jitter(cal, 50),
                    perceived_exertion=random.randint(8, 10), status="completed",
                )
                for oi, (ename, n_sets, reps, wt_today) in enumerate(
                        zip(exnames, [sets]*len(exnames), reps_list, weights)):
                    if ename not in EX: continue
                    we = WorkoutExercise.objects.create(workout=w, exercise=EX[ename], order=oi)
                    for s in range(1, n_sets + 1):
                        actual_wt = round_weight(wt_today * pf) if wt_today else None
                        ExerciseSet.objects.create(
                            workout_exercise=we, set_number=s,
                            reps=reps if reps else None,
                            weight=actual_wt,
                            duration_sec=reps if not wt_today and reps > 20 else None,
                            rpe=random.randint(7, 10), completed=True,
                        )

        self._log("Workouts seeded.")

    # ── Measurements ─────────────────────────────────────────────────────────

    def _create_measurements(self, u):
        from measurements.models import BodyMeasurement
        today = date.today()

        # (user, weeks, start_weight, weekly_delta, body_fat_start, rhr)
        configs = [
            ("alice",  24, 71.8, -0.11, 22.5, 56),  # cutting: -2.6kg over 24 weeks
            ("marcus", 16, 72.2,  0.00, 11.0, 48),  # stable runner weight
            ("sofia",  20, 78.0, -0.38, 31.0, 68),  # weight loss: -7.6kg over 20 weeks
            ("jake",    8, 85.0, -0.19, 20.0, 72),  # slow drop as beginner
            ("priya",  32, 58.0,  0.07, 18.5, 54),  # gaining muscle slowly
        ]
        for username, weeks, start_wt, delta, bf_start, rhr in configs:
            user = u[username]
            for week in range(weeks):
                rec_date = today - timedelta(weeks=week)
                weight   = round(start_wt + delta * week, 1)   # note: week=0 is today
                bf_pct   = round(bf_start - (weeks - week) * 0.05, 1)
                BodyMeasurement.objects.get_or_create(
                    user=user, recorded_at=rec_date,
                    defaults=dict(
                        weight_kg=weight,
                        body_fat_percent=max(8.0, bf_pct),
                        waist_cm=round(70 + weight * 0.3, 1),
                        resting_hr_bpm=rhr + random.randint(-3, 3),
                        steps=random.randint(6000, 14000) if username != "jake" else None,
                    ),
                )
        self._log("Measurements seeded.")

    # ── Nutrition ─────────────────────────────────────────────────────────────

    def _create_nutrition(self, u, food_map):
        from nutrition.models import Meal, MealItem, WaterLog
        today = timezone.now()

        # (user, days, meals_per_day, skip_rate, water_ml, meal_template)
        configs = [
            ("alice",  60, 4, 0.05, 2600, ALICE_MEALS),
            ("marcus", 60, 4, 0.07, 3200, MARCUS_MEALS),
            ("sofia",  90, 4, 0.03, 2000, SOFIA_MEALS),  # never misses a log
            ("jake",   21, 3, 0.30, 2200, JAKE_MEALS),   # inconsistent
            ("priya",  45, 4, 0.06, 2400, PRIYA_MEALS),
        ]
        meal_hours = {"breakfast": 7, "lunch": 12, "dinner": 19, "snack": 16}

        for username, days, meals_per_day, skip_rate, water, meal_tmpl in configs:
            user = u[username]
            for day in range(days):
                if random.random() < skip_rate:
                    continue
                dt = today - timedelta(days=day)
                meal_types = list(meal_tmpl.keys())[:meals_per_day]
                for mtype in meal_types:
                    consumed = dt.replace(hour=meal_hours[mtype], minute=0, second=0, microsecond=0)
                    meal = Meal.objects.create(user=user, meal_type=mtype, consumed_at=consumed)
                    for food_name, serving_base in meal_tmpl[mtype]:
                        food = food_map.get(food_name)
                        if food:
                            servings = round(serving_base + random.uniform(-0.2, 0.2), 2)
                            MealItem.objects.create(meal=meal, food=food, servings=max(0.5, servings))
                WaterLog.objects.create(
                    user=user,
                    amount_ml=water + random.randint(-300, 300),
                    logged_at=dt.replace(hour=20, minute=0, second=0, microsecond=0),
                )
        self._log("Nutrition seeded.")

    # ── Goals ─────────────────────────────────────────────────────────────────

    def _create_goals(self, u):
        from goals.models import Goal
        today = date.today()

        goal_sets = {
            "alice": [
                ("Bench Press 100kg",   "strength",          100, 70,  87.5, "kg",  today+timedelta(days=90),  "active"),
                ("Cut to 65kg",         "weight_loss",       65,  72,  67.2, "kg",  today+timedelta(days=60),  "active"),
                ("4 sessions per week", "workouts_per_week", 4,   0,   4,    "sessions", None,                 "active"),
                ("Hit 100 workouts",    "workout_count",     100, 0,   88,   "workouts", None,                 "active"),
            ],
            "marcus": [
                ("Sub-3:45 marathon",   "endurance",         225, 280, 248,  "min", today+timedelta(days=90),  "active"),
                ("Run 60km/week",       "endurance",         60,  0,   52,   "km",  None,                      "active"),
                ("Sub-50min 10K",       "endurance",         50,  65,  48,   "min", today-timedelta(days=14),  "achieved"),
            ],
            "sofia": [
                ("Reach 65kg",          "weight_loss",       65,  78,  70.2, "kg",  today+timedelta(days=90),  "active"),
                ("Log food every day",  "custom",            90,  0,   85,   "days", None,                     "active"),
                ("Lose first 5kg",      "weight_loss",       73,  78,  70.2, "kg",  today-timedelta(days=30),  "achieved"),
                ("Work out 3x/week",    "workouts_per_week", 3,   0,   3,    "sessions", None,                 "active"),
            ],
            "jake": [
                ("Survive the first month", "workout_count", 12, 0,   14,   "workouts", today-timedelta(days=5), "achieved"),
                ("Work out 3x/week",    "workouts_per_week", 3,  0,   2,    "sessions", today+timedelta(days=30), "active"),
                ("Lose 5kg",            "weight_loss",       80, 85,  83.5, "kg",  today+timedelta(days=90),  "active"),
            ],
            "priya": [
                ("Squat bodyweight×1.5","strength",          90,  58, 72.5, "kg",  today-timedelta(days=60),  "achieved"),
                ("100 CrossFit WODs",   "workout_count",     100, 0,  100,  "WODs",today-timedelta(days=20),  "achieved"),
                ("6-month streak",      "streak_days",       180, 0,  165,  "days",today+timedelta(days=30),  "active"),
                ("Deadlift 120kg",      "strength",          120, 75, 95,   "kg",  today+timedelta(days=60),  "active"),
                ("Compete in Open",     "custom",            1,   0,  1,    "event",today-timedelta(days=14), "achieved"),
            ],
        }

        for username, goals in goal_sets.items():
            user = u[username]
            for title, gtype, target, start, current, unit, deadline, status in goals:
                Goal.objects.get_or_create(
                    user=user, title=title,
                    defaults=dict(goal_type=gtype, target_value=target, starting_value=start,
                                  current_value=current, unit=unit, deadline=deadline,
                                  status=status),
                )
        self._log("Goals seeded.")

    # ── Social ────────────────────────────────────────────────────────────────

    def _create_social(self, u):
        from social.models import Comment, Like, Post

        today = timezone.now()

        # (username, body, days_ago)
        post_data = [
            # Alice — powerlifter updates
            ("alice",  "NEW BENCH PR: 87.5kg × 4 reps. 100kg is coming 🎯", 2),
            ("alice",  "Week 24 check-in: down 4.5kg since I started the cut. Strength staying strong 💪", 14),
            ("alice",  "Rest day means meal prep day. 12 containers of chicken and rice ready to go 🥗", 21),
            ("alice",  "Push day done. Overhead press is finally clicking after months of struggling 🏋️", 35),
            ("alice",  "6 months of logging every single session. This app keeps me honest. Here's to 6 more 🚀", 56),
            # Marcus — runner updates
            ("marcus", "28km long run this morning. Legs are absolutely cooked. 2 hours 32 mins 🏃", 3),
            ("marcus", "Speed session: 6×1km repeats averaging 3:55/km. Boston qualifier is within reach 💨", 10),
            ("marcus", "10K in 47:48! PR by 2 mins. Sub-45 is next 🔥", 30),
            ("marcus", "Week 12 of training. 52km this week. Body is adapting. Sleep is the real gains 😴", 45),
            ("marcus", "First 20km long run of the training block. Legs held up. Nutrition was on point 💧", 70),
            # Sofia — weight loss journey
            ("sofia",  "8kg down from where I started 🎉 Slow and steady. Tracking every macro every day.", 1),
            ("sofia",  "Hit my protein goal for 30 days straight. It's a habit now, not a chore 💚", 15),
            ("sofia",  "First time fitting into my old jeans in 2 years. This is why we do it 😭❤️", 32),
            ("sofia",  "Meal prep Sunday. Healthy eating doesn't have to be boring — today was teriyaki tofu 🍱", 50),
            ("sofia",  "5kg milestone: officially lost 5kg. 8 more to go. Halfway there! 🎯", 68),
            # Jake — beginner energy
            ("jake",   "Week 1 done!! Legs are DEAD but I'm proud. Starting something new is scary 🙏", 55),
            ("jake",   "Just hit 10 workouts total. A month ago I couldn't do 5 push-ups. Now I'm doing sets 💪", 30),
            ("jake",   "Down 1.5kg. Still figuring out the eating but the gym is becoming a habit fr 🏋️", 10),
            # Priya — CrossFit veteran
            ("priya",  "WOD today: 21-15-9 thrusters at 42.5kg + pull-ups. 8:43. New PR 💥", 1),
            ("priya",  "100 CrossFit WODs logged on FitTrack! Never thought I'd hit triple digits 🏆", 20),
            ("priya",  "Competed in the CrossFit Open this weekend. Placed 47th in the region. Not bad for a 'hobby' 😄", 42),
            ("priya",  "Squat 72.5kg × 5. 8 months ago that was my 1RM. Progress is beautiful 🙌", 65),
            ("priya",  "Morning crew showing up at 6am every day. This community is everything 💙", 90),
            ("priya",  "Deadlift 95kg today. 120kg is the goal. Getting closer every week 🔥", 105),
        ]

        post_objects = {}
        for username, body, days_ago in post_data:
            user = u[username]
            post = Post.objects.create(user=user, body=body)
            # Backdate the post
            Post.objects.filter(pk=post.pk).update(
                created_at=today - timedelta(days=days_ago)
            )
            post.refresh_from_db()
            post_objects[(username, body[:20])] = post

        all_posts = list(Post.objects.filter(user__in=u.values()).order_by("?"))

        # Realistic likes: each user likes posts from their friends
        like_pairs = [
            # (liker, post_owner, post_body_prefix)
            ("marcus", "alice",  "NEW BENCH PR"),
            ("priya",  "alice",  "NEW BENCH PR"),
            ("sofia",  "alice",  "6 months of logging"),
            ("jake",   "alice",  "Week 24 check-in"),
            ("alice",  "marcus", "28km long run"),
            ("priya",  "marcus", "28km long run"),
            ("sofia",  "marcus", "10K in 47:48"),
            ("jake",   "marcus", "10K in 47:48"),
            ("alice",  "sofia",  "8kg down"),
            ("marcus", "sofia",  "8kg down"),
            ("priya",  "sofia",  "8kg down"),
            ("alice",  "sofia",  "Hit my protein goal"),
            ("priya",  "sofia",  "First time fitting"),
            ("alice",  "jake",   "Week 1 done"),
            ("marcus", "jake",   "Week 1 done"),
            ("sofia",  "jake",   "Week 1 done"),
            ("priya",  "jake",   "Week 1 done"),
            ("alice",  "jake",   "Down 1.5kg"),
            ("alice",  "priya",  "WOD today: 21-15-9"),
            ("marcus", "priya",  "100 CrossFit WODs"),
            ("sofia",  "priya",  "100 CrossFit WODs"),
            ("jake",   "priya",  "100 CrossFit WODs"),
            ("alice",  "priya",  "Squat 72.5kg"),
            ("marcus", "priya",  "Morning crew"),
        ]
        for liker, post_owner, body_prefix in like_pairs:
            post = Post.objects.filter(user=u[post_owner], body__startswith=body_prefix).first()
            if post:
                Like.objects.get_or_create(post=post, user=u[liker])

        # Rich comments
        comments = [
            ("marcus", "alice",  "NEW BENCH PR",          "Bro that's incredible. I can barely lift the bar 😂"),
            ("priya",  "alice",  "NEW BENCH PR",          "100kg is YOURS. Lock it in 🔒🔥"),
            ("sofia",  "alice",  "Week 24 check-in",      "The cut AND keeping strength?! Goals honestly 💪"),
            ("jake",   "alice",  "6 months of logging",   "This is so motivating. You're the reason I started 🙏"),
            ("alice",  "marcus", "28km long run",         "28km?? I struggle at 5. Mad respect 🏃"),
            ("priya",  "marcus", "28km long run",         "That pace for 28km is elite. Boston watch out! 🏆"),
            ("sofia",  "marcus", "10K in 47:48",          "PR!! You absolutely smashed it!! 🎉"),
            ("alice",  "sofia",  "8kg down",              "EIGHT KG?! The dedication is unreal. So proud of you 💚"),
            ("marcus", "sofia",  "Hit my protein goal",   "30 days straight of hitting protein is wild discipline 🔥"),
            ("priya",  "sofia",  "First time fitting",    "THIS MADE ME EMOTIONAL. You deserve every bit of this 😭❤️"),
            ("jake",   "sofia",  "8kg down",              "This is exactly what I needed to see today. Thank you 💪"),
            ("alice",  "jake",   "Week 1 done",           "Week 1 is the hardest. You made it!! Keep going! 🚀"),
            ("sofia",  "jake",   "Week 1 done",           "I remember my week 1 like it was yesterday. The soreness is real 😂 You got this!"),
            ("priya",  "jake",   "Just hit 10 workouts",  "10 workouts in and already seeing changes? That's the magic 💥"),
            ("marcus", "jake",   "Down 1.5kg",            "Progress is progress. Don't compare your day 30 to anyone's day 300 👊"),
            ("alice",  "priya",  "WOD today: 21-15-9",    "8:43?! That's genuinely scary. I need to try CrossFit 😅"),
            ("sofia",  "priya",  "100 CrossFit WODs",     "100 WODs!! That's obsession in the best possible way 🏆"),
            ("jake",   "priya",  "100 CrossFit WODs",     "Goals! I hope I'm posting something like this in a year 🙌"),
            ("marcus", "priya",  "Competed in the CrossFit","47th in the region for a 'hobby'?? You're insane 😂 legendary"),
            ("alice",  "priya",  "Squat 72.5kg",          "From 72.5 as your 1RM to 72.5 for reps in 8 months. That's what hard work looks like 🙌"),
        ]
        for commenter, post_owner, body_prefix, comment_body in comments:
            post = Post.objects.filter(user=u[post_owner], body__startswith=body_prefix).first()
            if post:
                Comment.objects.get_or_create(
                    post=post, user=u[commenter],
                    defaults={"body": comment_body},
                )

        self._log("Social: posts, likes, and comments seeded.")

    # ── Achievements ──────────────────────────────────────────────────────────

    def _create_achievements(self, u):
        from achievements.models import Achievement, Streak, UserAchievement

        streak_data = {
            "alice":  (12, 45, date.today()),
            "marcus": (18, 28, date.today()),
            "sofia":  ( 5, 21, date.today()),
            "jake":   ( 2,  5, date.today()),
            "priya":  (22, 60, date.today()),
        }
        for username, (cur, longest, last) in streak_data.items():
            Streak.objects.update_or_create(
                user=u[username],
                defaults={"current_days": cur, "longest_days": longest, "last_workout_date": last},
            )

        # Each user unlocks badges that match their actual history
        unlock_map = {
            "alice": [
                "first_workout","workouts_10","workouts_25","workouts_50","workouts_100",
                "streak_3","streak_7","streak_14",
                "volume_1k","volume_5k","volume_10k","volume_25k",
                "minutes_100","minutes_300","minutes_600","minutes_1500","minutes_3000",
                "calories_1k","calories_5k",
                "early_bird_5","early_bird_20",
                "goals_1",
            ],
            "marcus": [
                "first_workout","workouts_10","workouts_25","workouts_50",
                "streak_3","streak_7","streak_14",
                "minutes_100","minutes_300","minutes_600","minutes_1500","minutes_3000",
                "calories_1k","calories_5k","calories_25k",
                "distance_5k","distance_21k","distance_42k","distance_100k","distance_500k",
                "early_bird_5","early_bird_20","early_bird_50",
                "goals_1","goals_5",
            ],
            "sofia": [
                "first_workout","workouts_10","workouts_25","workouts_50",
                "streak_3","streak_7","streak_14","streak_30",
                "minutes_100","minutes_300","minutes_600",
                "calories_1k","calories_5k",
                "goals_1",
            ],
            "jake": [
                "first_workout","workouts_10",
                "streak_3",
                "minutes_100",
                "calories_1k",
            ],
            "priya": [
                "first_workout","workouts_10","workouts_25","workouts_50","workouts_100","workouts_200",
                "streak_3","streak_7","streak_14","streak_30","streak_60",
                "volume_1k","volume_5k","volume_10k","volume_25k","volume_50k",
                "minutes_100","minutes_300","minutes_600","minutes_1500","minutes_3000","minutes_6000",
                "calories_1k","calories_5k","calories_25k","calories_100k",
                "early_bird_5","early_bird_20","early_bird_50",
                "goals_1","goals_5","goals_10",
            ],
        }
        all_achievements = {a.code: a for a in Achievement.objects.all()}
        for username, codes in unlock_map.items():
            user = u[username]
            for code in codes:
                if code in all_achievements:
                    UserAchievement.objects.get_or_create(user=user, achievement=all_achievements[code])

        self._log("Achievements and streaks seeded.")

    # ── Reminders ─────────────────────────────────────────────────────────────

    def _create_reminders(self, u):
        from reminders.models import Reminder

        reminder_data = {
            "alice": [
                ("Push Day", "workout", time( 6,30), ["mon"]),
                ("Pull Day", "workout", time( 6,30), ["wed"]),
                ("Leg Day",  "workout", time( 7, 0), ["thu"]),
                ("Upper",    "workout", time( 7, 0), ["sat"]),
                ("Protein Check", "meal", time(20, 0), ["mon","tue","wed","thu","fri","sat","sun"]),
                ("Weekly Weigh-In", "measurement", time(7,30), ["mon"]),
            ],
            "marcus": [
                ("Morning Run", "workout", time( 5,45), ["mon","tue","wed","thu","fri","sat"]),
                ("Post-Run Nutrition", "meal", time(7,30), ["mon","tue","wed","thu","fri","sat"]),
                ("Weekly Long Run", "workout", time(6, 0), ["sat"]),
            ],
            "sofia": [
                ("Log Breakfast",   "meal", time( 7,30), ["mon","tue","wed","thu","fri","sat","sun"]),
                ("Log Lunch",       "meal", time(12,30), ["mon","tue","wed","thu","fri","sat","sun"]),
                ("Log Dinner",      "meal", time(19,30), ["mon","tue","wed","thu","fri","sat","sun"]),
                ("Water Reminder",  "water", time(10, 0), ["mon","tue","wed","thu","fri"]),
                ("Water Reminder",  "water", time(15, 0), ["mon","tue","wed","thu","fri"]),
                ("Workout — Mon",   "workout", time(7,30), ["mon"]),
                ("Workout — Wed",   "workout", time(7,30), ["wed"]),
                ("Workout — Fri",   "workout", time(7,30), ["fri"]),
                ("Weekly Weigh-In", "measurement", time(7, 0), ["fri"]),
            ],
            "jake": [
                ("Gym Time",  "workout", time(18, 0), ["mon","wed"]),
                ("Drink Water", "water", time(12, 0), ["mon","tue","wed","thu","fri"]),
            ],
            "priya": [
                ("Morning WOD", "workout", time( 5,45), ["mon","tue","thu","fri","sat"]),
                ("Pre-WOD Meal", "meal",   time( 5, 0), ["mon","tue","thu","fri","sat"]),
                ("Weekly Weigh-In", "measurement", time(7,30), ["mon"]),
                ("Mobility Work", "workout", time(20, 0), ["wed","sun"]),
            ],
        }
        for username, reminders in reminder_data.items():
            user = u[username]
            for title, rtype, tod, days in reminders:
                Reminder.objects.get_or_create(
                    user=user, title=title, time_of_day=tod,
                    defaults={"reminder_type": rtype, "days_of_week": days, "is_active": True},
                )
        self._log("Reminders seeded.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, msg):
        self.stdout.write(f"  {msg}")

    def _print_credentials(self):
        self.stdout.write("\n" + self.style.SUCCESS("=" * 68))
        self.stdout.write(self.style.SUCCESS("  Demo users ready  ·  Password: nepal@123"))
        self.stdout.write(self.style.SUCCESS("=" * 68))
        rows = [
            ("alice",  "Alice Chen",       "Powerlifter · 6-month cut · very social · 24wk history"),
            ("marcus", "Marcus Webb",      "Marathon runner · Boston qualifier training · 16wk history"),
            ("sofia",  "Sofia Rodriguez",  "Weight-loss journey · -8kg · logs every meal · 20wk history"),
            ("jake",   "Jake Turner",      "Beginner · 2 months in · inconsistent · minimal data"),
            ("priya",  "Priya Kapoor",     "CrossFit · 8 months · most data · 20+ achievements"),
        ]
        for username, name, note in rows:
            self.stdout.write(f"  {username:<8} {name:<20} {note}")
        self.stdout.write(self.style.SUCCESS("=" * 68) + "\n")


# ── Module-level helpers ──────────────────────────────────────────────────────

def _skip(username: str, week: int, day: int, skip_pct: int) -> bool:
    """Deterministic skip — same seed → same workouts every run."""
    return abs(hash((username, week, day))) % 100 < skip_pct


def _jitter(base: int, spread: int) -> int:
    return base + random.randint(-spread, spread)


def round_weight(w: float) -> float:
    """Round to nearest 2.5 kg (standard plate increment)."""
    if not w:
        return None
    return round(round(w / 2.5) * 2.5, 1)
