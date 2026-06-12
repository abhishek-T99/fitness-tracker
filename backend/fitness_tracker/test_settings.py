from fitness_tracker.settings import *  # noqa: F401, F403

# Fast in-memory cache — no Redis required during tests.
# PatternLocMemCache adds the delete_pattern method that django-redis signals use.
CACHES = {
    "default": {
        "BACKEND": "fitness_tracker.test_cache.PatternLocMemCache",
    }
}

# Emails land in django.core.mail.outbox instead of being sent
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Run Celery tasks synchronously so tests can assert on their side effects
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# MD5 is fast and sufficient for test data — never use in production
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Keep media uploads in a temp directory so test runs don't pollute the repo
import tempfile  # noqa: E402
MEDIA_ROOT = tempfile.mkdtemp()
