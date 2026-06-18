# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

Django 5 + DRF + SimpleJWT + Celery 5 backend, React 18 + Vite 5 + Tailwind + TanStack Query frontend, Redis as broker/cache, SQLite as the default DB. Whole stack runs via `docker compose up --build` (5 services: `redis`, `backend`, `worker`, `beat`, `frontend`).

## Common commands

Docker (preferred — `backend` auto-migrates and re-seeds on every boot):

```bash
docker compose up --build                          # full stack on :5173 (frontend) and :8000 (backend)
docker compose logs -f backend worker beat
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py test <app>        # run a single app's tests
docker compose exec backend python manage.py test <app>.tests.SomeTest.test_x
docker compose down -v                             # nuke DB + redis + media
```

Local backend (Python 3.10+, Redis on 6379):

```powershell
cd backend
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_exercises ; python manage.py seed_foods ; python manage.py seed_achievements
python manage.py runserver
# in separate shells:
celery -A fitness_tracker worker -l info
celery -A fitness_tracker beat -l info
```

Local frontend:

```powershell
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api → backend
npm run build        # production bundle
```

There is no lint/format script wired up in either package; don't invent one.

## Architecture — things you can't see by reading one file

### Backend app layout

Each domain is a Django app under `backend/`: `accounts`, `exercises`, `workouts`, `nutrition`, `measurements`, `goals`, `social`, `achievements`, `reminders`. They're mounted at `/api/v1/<app>/` from `fitness_tracker/urls.py`. Custom user model: `accounts.User` (set via `AUTH_USER_MODEL`).

Auth is JWT (SimpleJWT) with refresh-token rotation. Everything except `register` / `login` / `refresh` requires `Authorization: Bearer <access>`.

### Celery topology

Three roles share one image, dispatched by `backend/entrypoint.sh {web|worker|beat|migrate}`:

- `web` — waits for Redis, runs `migrate`, runs idempotent seed commands (`seed_exercises`, `seed_foods`, `seed_achievements`), then `runserver` (DEBUG) or `gunicorn` (else).
- `worker` — `celery -A fitness_tracker worker`.
- `beat` — `celery -A fitness_tracker beat` using `django_celery_beat.schedulers:DatabaseScheduler` (so periodic schedules live in the DB; migrations must run first).

Static beat schedule is defined in `fitness_tracker/settings.py → CELERY_BEAT_SCHEDULE`:

| Cron                  | Task                                       |
|-----------------------|--------------------------------------------|
| every minute          | `reminders.tasks.dispatch_due_reminders`   |
| daily 02:15 UTC       | `achievements.tasks.decay_inactive_streaks` |
| daily 02:30 UTC       | `goals.tasks.mark_expired_goals`           |
| Mondays 08:00 UTC     | `accounts.tasks.build_weekly_summaries`    |

Set `CELERY_TASK_ALWAYS_EAGER=True` in `.env` to run tasks inline (useful for tests).

The reminders **delivery** layer in `reminders.tasks.deliver_reminder` is intentionally a `logger.info` stub — swap it for push/email/websocket when needed. The dispatcher is wired.

### Caching contract (important — don't bypass)

All cache keys + TTLs live in **`fitness_tracker/cache_keys.py`**. Read paths and the per-app `signals.py` modules import from there — if you add a cached read, add the key here and a matching invalidation signal. Do not hardcode cache key strings elsewhere.

`django-redis` is configured with `IGNORE_EXCEPTIONS=True`, so a Redis outage degrades caching silently rather than 500-ing the API. Don't change this without a reason.

Cached paths today: exercise catalog (24h), achievement catalog (24h), public foods (6h), per-user workout stats (5m), per-user-per-date nutrition summary (2m), per-user streak (5m), per-user weekly summary (~8d, rewritten by Mon beat task).

### Frontend data flow

`frontend/src/api/client.js` is an axios instance with a JWT refresh interceptor; `endpoints.js` wraps each REST resource. Server state is **TanStack Query** — mutations must invalidate the relevant query keys so the UI stays consistent without manual refetches. `AuthContext` (in `contexts/`) holds the access token and current user.

Vite dev server proxies `/api` and `/media` to `VITE_API_PROXY_TARGET` (defaults to `http://backend:8000` inside compose, `http://127.0.0.1:8000` locally). File watching uses polling — required for hot-reload across the Windows/macOS bind mount.

### Seeds and SQLite

Seeds use `update_or_create`, so re-running them is safe. The SQLite DB lives at `backend/db.sqlite3` and is bind-mounted from the host (`./backend:/app` in compose), so it survives `docker compose down` but is wiped by `docker compose down -v` (named volumes go too).

To switch to Postgres: add a `postgres` service, point `DATABASES["default"]` at it, drop the SQLite file. No other code changes needed (per README).

## graphify

This project has a live knowledge graph at `graphify-out/` covering all backend and frontend source. It is the **primary navigation tool** — use it before reaching for grep, glob, or raw file reads.

### Step 1 — Orient before every task

Before reading any source file, running a search, or answering an architecture question:

1. Read **`graphify-out/GRAPH_REPORT.md`** — god nodes, community clusters, cross-file edges at a glance.
2. If **`graphify-out/wiki/index.md`** exists, navigate the wiki articles (one per community) instead of raw files.

### Step 2 — Search with graphify, not grep

| When you need to… | Use |
|---|---|
| Understand how a feature/module works | `graphify query "<question>"` |
| Trace a call chain or data flow | `graphify query "<question>" --dfs` |
| Find the shortest link between two concepts | `graphify path "<A>" "<B>"` |
| Get a plain-English explanation of a node | `graphify explain "<concept>"` |
| Wide context sweep | `graphify query "<question>" --budget 1500` |

Only fall back to `Grep` / `Glob` when you need an exact symbol name or line number that graphify doesn't return.

### Step 3 — Keep the graph current after edits

Run **`graphify update .`** after every batch of file edits (AST-only, no API cost, ~2 s). A `PostToolUse` hook in `.claude/settings.json` fires this automatically after each `Edit` or `Write` call. If you make several changes before querying, or the hook fails, run it manually:

```bash
graphify update .
```
