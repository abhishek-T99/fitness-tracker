from django.apps import AppConfig


class AIConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai"
    verbose_name = "AI Assistant"

    def ready(self):
        # Importing the tools package triggers @tool registrations.
        from . import tools  # noqa: F401
