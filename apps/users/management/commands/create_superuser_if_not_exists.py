from django.core.management.base import BaseCommand, CommandError

from apps.users.models import User


class Command(BaseCommand):
    help = "Create a Django superuser from environment variables if it does not exist."

    def handle(self, *args, **options):
        email = (
            self._get_env_value("DJANGO_SUPERUSER_EMAIL")
            or self._get_env_value("SUPERUSER_EMAIL")
        )
        password = (
            self._get_env_value("DJANGO_SUPERUSER_PASSWORD")
            or self._get_env_value("SUPERUSER_PASSWORD")
        )
        first_name = (
            self._get_env_value("DJANGO_SUPERUSER_FIRST_NAME")
            or "Admin"
        )
        last_name = (
            self._get_env_value("DJANGO_SUPERUSER_LAST_NAME")
            or "User"
        )

        if not email:
            raise CommandError("DJANGO_SUPERUSER_EMAIL is required.")

        if not password:
            raise CommandError("DJANGO_SUPERUSER_PASSWORD is required.")

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Superuser with email {email} already exists."
                )
            )
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Superuser {email} created successfully.")
        )

    def _get_env_value(self, name):
        import os

        value = os.environ.get(name)

        if value:
            return value.strip()

        return None
