from django.core.management.base import BaseCommand

from apps.bookings.services.booking import complete_expired_bookings


class Command(BaseCommand):
    """Mark confirmed bookings as completed after checkout."""

    help = "Complete confirmed bookings whose end date has passed."

    def handle(self, *args, **options):
        updated_count = complete_expired_bookings()
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed bookings updated: {updated_count}"
            )
        )
