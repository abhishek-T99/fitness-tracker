from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

PW_USERNAME = "pw_testuser"
PW_EMAIL    = "pw_testuser@fittrack.test"
PW_PASSWORD = "TestPass123!"


class Command(BaseCommand):
    help = "Create or reset the Playwright E2E test user (always active, no email verification needed)"

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username=PW_USERNAME,
            defaults={
                "email":      PW_EMAIL,
                "first_name": "Playwright",
                "last_name":  "Tester",
                "is_active":  True,
            },
        )
        if not created:
            user.email      = PW_EMAIL
            user.is_active  = True
            user.first_name = "Playwright"
            user.last_name  = "Tester"

        user.set_password(PW_PASSWORD)
        user.save()

        from accounts.models import Profile  # noqa: PLC0415
        Profile.objects.get_or_create(user=user)

        verb = "Created" if created else "Reset"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} test user  username={PW_USERNAME}  password={PW_PASSWORD}"
        ))
