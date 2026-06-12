# FitTrack — A Comprehensive Fitness Tracker

A full-stack fitness application with a **Django REST + JWT** backend and a **React + Vite + Tailwind** frontend, with **Celery + Redis** powering async work and caching. Spins up end-to-end with `docker compose up`.

Tracks workouts, nutrition, body measurements, goals, social posts, achievements, and reminders — all in one place.

---

## Features

- **Auth** — JWT login/register with refresh-token rotation.
- **Workouts** — Log strength + cardio sessions with sets, reps, weight, RPE, and notes.
- **Routine templates** — Save reusable workouts.
- **Exercise library** — 30+ seeded exercises across all major muscle groups (search + filter).
- **Nutrition** — Log meals from a food database, daily calorie/macro breakdown, water tracking.
- **Body measurements** — Weight, body fat, circumferences, BMI, weight-history chart.
- **Goals** — Multiple goal types (weight, strength, weekly workouts…) with progress bars.
- **Social feed** — Posts, comments, likes, friends, friend requests, user search.
- **Achievements & streaks** — Automatic unlocks based on workout count, streak days, total volume, and minutes.
- **Reminders** — Per-user scheduled prompts (workout, water, meal, custom) — dispatched by Celery Beat every minute.
- **Profile & preferences** — Body stats, units (metric/imperial), calorie goal, timezone.

---

## Quick start (Docker)

> Requires Docker Desktop (or any Docker engine with Compose v2).

```bash
docker compose up --build
```

That single command brings up:

| Service     | Port  | Role                                         |
|-------------|-------|----------------------------------------------|
| `redis`     | 6379  | Broker for Celery + Django cache backend     |
| `backend`   | 8000  | Django REST API (auto-migrates + seeds)      |
| `worker`    | —     | Celery worker (async tasks)                  |
| `beat`      | —     | Celery Beat scheduler (periodic tasks)       |
| `frontend`  | 5173  | Vite dev server (hot reload over bind mount) |

Open **http://localhost:5173** — the Vite dev server proxies `/api` to `backend:8000` over the Docker network.

The backend container runs migrations and re-runs the idempotent seed commands on every boot.

### Day-to-day commands

```bash
# Tail logs
docker compose logs -f backend worker beat

# Create a superuser
docker compose exec backend python manage.py createsuperuser

# Run a one-off management command
docker compose exec backend python manage.py shell

# Reset everything (DB + redis + media)
docker compose down -v
```

---

## Local (non-Docker) setup

### Backend

> Python 3.10+, Redis 6+ running on `localhost:6379`

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # PowerShell
# source .venv/bin/activate           # macOS/Linux

pip install -r requirements.txt
copy .env.example .env                # cp on macOS/Linux

python manage.py migrate
python manage.py seed_exercises
python manage.py seed_foods
python manage.py seed_achievements
python manage.py createsuperuser      # optional, for /admin

python manage.py runserver
```

In separate terminals (worker + beat):

```bash
celery -A fitness_tracker worker -l info
celery -A fitness_tracker beat -l info
```

### Frontend

```powershell
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

---

## Architecture

### Backend (Django + DRF + Celery)

```
backend/
├── fitness_tracker/      project config + celery app + cache_keys registry
├── accounts/             custom User + Profile + JWT views + weekly summary task
├── exercises/            cached catalog + signal-based invalidation
├── workouts/             sessions, routines, async achievement triggers
├── nutrition/            foods, meals, water, cached daily summary
├── measurements/         body weight + BMI + history
├── goals/                goal tracking + deadline-check Beat task
├── social/               friendships, posts, comments, likes
├── achievements/         catalog + streak + async evaluator
└── reminders/            schedules + per-minute Beat dispatcher
```

### Async work (Celery)

| Trigger                  | Task                                          | What it does                                                |
|--------------------------|-----------------------------------------------|-------------------------------------------------------------|
| **Workout completed**    | `achievements.evaluate_workout`               | Recompute totals, update streak, unlock badges              |
| **Every minute (Beat)**  | `reminders.dispatch_due_reminders`            | Fire user reminders matching local time + day of week       |
| **Daily 02:15 (Beat)**   | `achievements.decay_inactive_streaks`         | Reset streaks for users who skipped a day                   |
| **Daily 02:30 (Beat)**   | `goals.mark_expired_goals`                    | Auto-mark goals whose deadline passed if target was hit     |
| **Mondays 08:00 (Beat)** | `accounts.build_weekly_summaries`             | Precompute + cache per-user weekly progress reports         |

Schedule lives in `fitness_tracker/settings.py → CELERY_BEAT_SCHEDULE`.

### Caching (Redis via `django-redis`)

Cached at the **hot, expensive** paths only — not blanket. All keys are managed in `fitness_tracker/cache_keys.py`:

| Cache key                                | TTL  | Invalidated by                                          |
|------------------------------------------|------|---------------------------------------------------------|
| `exercises:list:<query-hash>`            | 24h  | `exercises.signals` on `Exercise` save/delete           |
| `achievements:catalog:v1`                | 24h  | `achievements.signals` on `Achievement` save/delete     |
| `workout_stats:<user>`                   | 5m   | `workouts.signals` on `Workout` / `ExerciseSet` writes  |
| `streak:<user>`                          | 5m   | `achievements.signals` on `Streak` / unlock save        |
| `nutrition:summary:<user>:<date>`        | 2m   | `nutrition.signals` on `Meal` / `MealItem` / `WaterLog` |
| `weekly_summary:<user>`                  | ~8d  | Rewritten weekly by Beat task                           |

`django-redis` is configured with `IGNORE_EXCEPTIONS=True` — a Redis blip degrades caching but never takes down the API.

### Frontend

```
frontend/src/
├── api/                  axios client (JWT refresh interceptor) + endpoint helpers
├── contexts/             AuthContext
├── components/           AppLayout, ProtectedRoute, StatCard, …
└── pages/                Dashboard, Workouts, Nutrition, Measurements, Goals,
                          Social, Achievements, Reminders, Profile, …
```

Server state is managed with **TanStack Query** — mutations invalidate the relevant queries so the UI stays consistent without manual refetching.

---

## Key endpoints

| Method     | Path                                            | Purpose                                  |
|------------|-------------------------------------------------|------------------------------------------|
| POST       | `/api/v1/auth/register/`                        | Create user + receive JWT tokens         |
| POST       | `/api/v1/auth/login/`                           | Obtain `access` + `refresh` tokens       |
| POST       | `/api/v1/auth/refresh/`                         | Rotate the access token                  |
| GET/PATCH  | `/api/v1/auth/me/`                              | Current user (with embedded profile)     |
| GET        | `/api/v1/exercises/`                            | Exercise library (filter + search)       |
| CRUD       | `/api/v1/workouts/`                             | Workout sessions (nested sets)           |
| GET        | `/api/v1/workouts/stats/`                       | Weekly + last-14-days summary (cached)   |
| CRUD       | `/api/v1/workouts/routines/`                    | Reusable templates                       |
| CRUD       | `/api/v1/nutrition/foods/` `meals/` `water/`    | Nutrition                                |
| GET        | `/api/v1/nutrition/meals/daily_summary/`        | Daily macros (cached, ?date=YYYY-MM-DD)  |
| CRUD       | `/api/v1/measurements/`                         | Body metrics                             |
| CRUD       | `/api/v1/goals/`                                | Goal tracking                            |
| GET        | `/api/v1/social/posts/`                         | Feed                                     |
| POST       | `/api/v1/social/posts/{id}/like/` `/comment/`   | Engage                                   |
| CRUD       | `/api/v1/social/friendships/`                   | Friend requests                          |
| GET        | `/api/v1/achievements/catalog/` `unlocked/` `streak/` | Achievements                       |
| CRUD       | `/api/v1/reminders/`                            | Reminders                                |

All routes (except `register`, `login`, `refresh`) require an `Authorization: Bearer <access>` header.

---

## Tech stack

**Backend** — Django 5 · DRF 3.15 · djangorestframework-simplejwt · django-cors-headers · django-filter · Celery 5 · Redis 5 · django-redis · django-celery-beat · gunicorn · SQLite (default)

**Frontend** — React 18 · Vite 5 · React Router 6 · TanStack Query · Tailwind CSS 3 · React Hook Form · Recharts · Lucide · React Hot Toast · date-fns · Axios

**Infrastructure** — Docker Compose with 5 services (redis, backend, worker, beat, frontend). Healthchecks gate startup order; named volumes persist Redis + media.

---

## Notes

- Seeds are idempotent (`update_or_create`) — re-running the entrypoint script never duplicates data.
- The reminder *dispatcher* is wired; the *delivery* layer is intentionally a `logger.info` stub. Swap in web-push, FCM, email, or a websocket fan-out where `reminders.tasks.deliver_reminder` runs.
- To switch SQLite → Postgres, add a `postgres` service, point `DATABASES["default"]` at it, and remove the SQLite file. No code changes needed elsewhere.
- For a production-style frontend build (static + nginx instead of Vite dev server), replace the `frontend` service in compose with a multi-stage `nginx:alpine` image serving `npm run build` output.
