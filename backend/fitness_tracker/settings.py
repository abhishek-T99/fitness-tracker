"""Django settings for the fitness_tracker project."""
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1", "fitnesstracker.local"])

INSTALLED_APPS = [
    "jazzmin",           # must be before django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_celery_beat",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    # Local apps
    "accounts",
    "exercises",
    "workouts",
    "nutrition",
    "measurements",
    "goals",
    "social",
    "achievements",
    "reminders",
    "notifications",
    "integrations",
    "meal_plans",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "accounts.middleware.ActivityTrackingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fitness_tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "fitness_tracker.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "fittrack"),
        "USER": os.getenv("DB_USER", "fittrack"),
        "PASSWORD": os.getenv("DB_PASSWORD", "fittrack"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"   # UTC+5:45
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "fitness_tracker.pagination.FlexPageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ---------------------------------------------------------------------------
# drf-spectacular (OpenAPI 3 schema + Swagger / ReDoc UI)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "FitTrack API",
    "DESCRIPTION": (
        "REST API for the FitTrack fitness tracker application.\n\n"
        "All endpoints except **`/api/v1/auth/register/`**, "
        "**`/api/v1/auth/login/`**, and **`/api/v1/auth/refresh/`** "
        "require an `Authorization: Bearer <access_token>` header."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Separate request/response schemas where they differ (e.g. MeView GET vs PATCH).
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
    # Serve Swagger/ReDoc assets from the sidecar package — no CDN required.
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "TAGS": [
        {"name": "Auth", "description": "Registration, login, and profile management."},
        {"name": "Exercises", "description": "Read-only exercise catalog (cached 24 h)."},
        {"name": "Workouts", "description": "Workout sessions and reusable routines."},
        {"name": "Nutrition", "description": "Food database, meal logging, water intake, and daily macro summaries."},
        {"name": "Measurements", "description": "Body measurements and weight-history charts."},
        {"name": "Goals", "description": "Personal fitness goals with deadline and progress tracking."},
        {"name": "Social", "description": "Friend connections and activity feed."},
        {"name": "Achievements", "description": "Achievement catalog, unlocked badges, and workout streaks."},
        {"name": "Reminders", "description": "Scheduled workout and nutrition reminders."},
    ],
}

# ---------------------------------------------------------------------------
# django-jazzmin — custom admin UI
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "FitTrack Admin",
    "site_header": "FitTrack",
    "site_brand": "FitTrack",
    "site_logo": None,
    "site_icon": None,
    "welcome_sign": "Welcome to FitTrack Admin",
    "copyright": "FitTrack",
    "search_model": ["accounts.User", "workouts.Workout", "exercises.Exercise"],
    "user_avatar": "avatar",

    # Top navigation bar
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/docs/", "new_window": True},
{"model": "accounts.User"},
        {"app": "workouts"},
    ],

    # Sidebar settings
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Sidebar app/model ordering
    "order_with_respect_to": [
        "accounts",
        "workouts",
        "exercises",
        "nutrition",
        "measurements",
        "goals",
        "achievements",
        "social",
        "reminders",
        "django_celery_beat",
        "auth",
    ],

    # FontAwesome icons per model
    "icons": {
        "accounts": "fas fa-users-cog",
        "accounts.user": "fas fa-user",
        "accounts.profile": "fas fa-id-card",
        "exercises": "fas fa-dumbbell",
        "exercises.exercise": "fas fa-dumbbell",
        "workouts": "fas fa-fire",
        "workouts.workout": "fas fa-fire",
        "workouts.workoutexercise": "fas fa-list-ul",
        "workouts.routine": "fas fa-calendar-check",
        "nutrition": "fas fa-utensils",
        "nutrition.food": "fas fa-apple-alt",
        "nutrition.meal": "fas fa-bowl-food",
        "nutrition.waterlog": "fas fa-droplet",
        "measurements": "fas fa-weight-scale",
        "measurements.bodymeasurement": "fas fa-weight-scale",
        "goals": "fas fa-bullseye",
        "goals.goal": "fas fa-bullseye",
        "achievements": "fas fa-trophy",
        "achievements.achievement": "fas fa-trophy",
        "achievements.userachievement": "fas fa-medal",
        "achievements.streak": "fas fa-fire-flame-curved",
        "social": "fas fa-users",
        "social.post": "fas fa-newspaper",
        "social.friendship": "fas fa-user-group",
        "social.comment": "fas fa-comment",
        "social.like": "fas fa-heart",
        "reminders": "fas fa-bell",
        "reminders.reminder": "fas fa-bell",
        "django_celery_beat": "fas fa-clock",
        "django_celery_beat.periodictask": "fas fa-tasks",
        "django_celery_beat.crontabschedule": "fas fa-calendar-alt",
        "django_celery_beat.intervalschedule": "fas fa-redo",
        "auth": "fas fa-shield-halved",
        "auth.group": "fas fa-users-gear",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # Open related model in a modal instead of a new page
    "related_modal_active": True,

    # Custom static assets
    "custom_css": "admin/css/jazzmin-fittrack.css",
    "custom_js": None,

    # Disable the theme builder UI — we control the theme via settings
    "show_ui_builder": False,

    # Change-form layout
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "accounts.user": "collapsible",
    },
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-outline-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    ["https://fitnesstracker.local", "http://localhost:5173", "http://127.0.0.1:5173"],
)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    ["https://fitnesstracker.local", "http://localhost:5173", "http://127.0.0.1:5173"],
)

# Trust the X-Forwarded-Proto header set by Nginx so Django knows the
# original request was HTTPS even though Nginx talks to it over HTTP.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# ---------------------------------------------------------------------------
# Cache (Redis-backed via django-redis)
# ---------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # never let a Redis hiccup take down the API
        },
        "KEY_PREFIX": "fittrack",
        "TIMEOUT": 300,
    }
}
DJANGO_REDIS_IGNORE_EXCEPTIONS = True

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "FitTrack <noreply@fittrack.app>")

# Public URL of the frontend — used to build links inside outgoing emails.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# ---------------------------------------------------------------------------
# Social auth (Google + Facebook)
# ---------------------------------------------------------------------------
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")

# YouTube Data API v3 (exercise tutorials)
# ---------------------------------------------------------------------------
# Get a free key at https://console.cloud.google.com → Enable YouTube Data API v3
# Free tier: 10,000 units/day. Search = 100 units. Results cached 24 h in Redis.
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# Strava integration
# ---------------------------------------------------------------------------
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
# A secret string you choose; must match what you enter in the Strava webhook
# subscription registration call.
STRAVA_WEBHOOK_VERIFY_TOKEN = os.getenv("STRAVA_WEBHOOK_VERIFY_TOKEN", "fittrack-strava-verify")

# Static schedule (in addition to whatever lives in the DB scheduler).
CELERY_BEAT_SCHEDULE = {
    "dispatch-due-reminders-every-minute": {
        "task": "reminders.tasks.dispatch_due_reminders",
        "schedule": crontab(minute="*"),
    },
    "decay-streaks-daily": {
        "task": "achievements.tasks.decay_inactive_streaks",
        "schedule": crontab(hour=2, minute=15),  # 02:15 UTC
    },
    "auto-mark-goal-deadlines-daily": {
        "task": "goals.tasks.mark_expired_goals",
        "schedule": crontab(hour=2, minute=30),
    },
    "weekly-progress-summary": {
        "task": "accounts.tasks.build_weekly_summaries",
        "schedule": crontab(hour=8, minute=0, day_of_week="mon"),  # Mon 08:00 UTC
    },
    "notify-streak-at-risk-daily": {
        "task": "notifications.tasks.notify_streak_at_risk",
        "schedule": crontab(hour=20, minute=0),  # 20:00 UTC — evening check
    },
    "notify-goal-deadlines-daily": {
        "task": "notifications.tasks.notify_goal_deadlines",
        "schedule": crontab(hour=9, minute=0),  # 09:00 UTC — morning nudge
    },
    "sync-intervals-activities-every-6h": {
        # Polls all active Intervals.icu integrations for new activities.
        # Webhooks handle real-time; this is the safety net for missed events.
        "task": "integrations.tasks.sync_all_intervals_integrations",
        "schedule": crontab(minute=0, hour="*/6"),  # every 6 hours
    },
}
