#!/usr/bin/env bash
# Entrypoint dispatcher used by every backend container in docker-compose.
# Usage: ./entrypoint.sh {web|worker|beat|migrate}
set -euo pipefail

ROLE="${1:-web}"

wait_for_redis() {
  python - <<'PY'
import os, sys, time
import redis
url = os.getenv("REDIS_URL", "redis://redis:6379/0")
for attempt in range(30):
    try:
        redis.from_url(url).ping()
        print(f"redis ready at {url}")
        sys.exit(0)
    except Exception as exc:
        print(f"waiting for redis ({attempt+1}/30): {exc}")
        time.sleep(1)
print("redis did not become ready in time")
sys.exit(1)
PY
}

wait_for_postgres() {
  python - <<'PY'
import os, sys, time
import psycopg2
host     = os.getenv("DB_HOST", "127.0.0.1")
port     = os.getenv("DB_PORT", "5432")
dbname   = os.getenv("DB_NAME", "fittrack")
user     = os.getenv("DB_USER", "fittrack")
password = os.getenv("DB_PASSWORD", "fittrack")
for attempt in range(30):
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
        conn.close()
        print(f"postgres ready at {host}:{port}/{dbname}")
        sys.exit(0)
    except Exception as exc:
        print(f"waiting for postgres ({attempt+1}/30): {exc}")
        time.sleep(1)
print("postgres did not become ready in time")
sys.exit(1)
PY
}

case "$ROLE" in
  web)
    wait_for_redis
    wait_for_postgres
    python manage.py migrate --noinput
    # Idempotent seed — safe to re-run on every boot.
    python manage.py seed_exercises
    python manage.py seed_foods
    python manage.py seed_achievements
    if [ "${DEBUG:-True}" = "True" ]; then
      exec python manage.py runserver 0.0.0.0:8000
    else
      python manage.py collectstatic --noinput
      exec gunicorn fitness_tracker.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --access-logfile - \
        --error-logfile -
    fi
    ;;
  worker)
    wait_for_redis
    wait_for_postgres
    exec celery -A fitness_tracker worker --loglevel=info --concurrency="${CELERY_CONCURRENCY:-2}"
    ;;
  beat)
    wait_for_redis
    wait_for_postgres
    # django-celery-beat keeps its schedule in the DB; migrations must exist first.
    python manage.py migrate --noinput
    exec celery -A fitness_tracker beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    ;;
  migrate)
    wait_for_redis
    wait_for_postgres
    exec python manage.py migrate --noinput
    ;;
  *)
    echo "unknown role: $ROLE (expected: web|worker|beat|migrate)" >&2
    exit 1
    ;;
esac
