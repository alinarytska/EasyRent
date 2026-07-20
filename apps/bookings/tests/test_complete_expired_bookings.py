from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.bookings.models import Booking
from apps.bookings.services.booking import complete_expired_bookings
from apps.listings.models import Listing
from apps.users.models import User


class CompleteExpiredBookingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        cls.renter = User.objects.create_user(
            email="renter@example.com",
            password="strong-test-password",
            first_name="John",
            last_name="Brown",
        )
        cls.listing = Listing.objects.create(
            owner=cls.owner,
            title="Apartment in Berlin",
            description="Bright apartment near the city center.",
            property_type=Listing.PropertyType.APARTMENT,
            price_per_night=Decimal("120.00"),
            rooms=2,
            city="Berlin",
            district="Mitte",
            postal_code="10115",
            street="Invalidenstrasse",
            house_number="1",
        )

    def create_booking(self, **overrides):
        today = timezone.localdate()
        data = {
            "listing": self.listing,
            "renter": self.renter,
            "start_date": today - timedelta(days=3),
            "end_date": today,
            "price_per_night": Decimal("120.00"),
            "total_price": Decimal("360.00"),
            "status": Booking.Status.CONFIRMED,
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def test_complete_expired_bookings_completes_confirmed_bookings_due_today(self):
        booking = self.create_booking(status=Booking.Status.CONFIRMED)

        updated_count = complete_expired_bookings()

        self.assertEqual(updated_count, 1)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.COMPLETED)

    def test_complete_expired_bookings_completes_past_confirmed_bookings(self):
        today = timezone.localdate()
        booking = self.create_booking(
            start_date=today - timedelta(days=5),
            end_date=today - timedelta(days=2),
            status=Booking.Status.CONFIRMED,
        )

        updated_count = complete_expired_bookings()

        self.assertEqual(updated_count, 1)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.COMPLETED)

    def test_complete_expired_bookings_keeps_future_confirmed_bookings(self):
        today = timezone.localdate()
        booking = self.create_booking(
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=4),
            status=Booking.Status.CONFIRMED,
        )

        updated_count = complete_expired_bookings()

        self.assertEqual(updated_count, 0)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_complete_expired_bookings_updates_only_confirmed_bookings(self):
        statuses = (
            Booking.Status.PENDING,
            Booking.Status.REJECTED,
            Booking.Status.CANCELLED,
            Booking.Status.COMPLETED,
        )
        bookings = [
            self.create_booking(
                start_date=timezone.localdate() - timedelta(days=index + 5),
                end_date=timezone.localdate() - timedelta(days=index + 1),
                status=status,
            )
            for index, status in enumerate(statuses)
        ]

        updated_count = complete_expired_bookings()

        self.assertEqual(updated_count, 0)

        for booking, status in zip(bookings, statuses):
            booking.refresh_from_db()
            self.assertEqual(booking.status, status)

    def test_complete_expired_bookings_command_outputs_updated_count(self):
        self.create_booking(status=Booking.Status.CONFIRMED)
        output = StringIO()

        call_command("complete_expired_bookings", stdout=output)

        self.assertIn("Completed bookings updated: 1", output.getvalue())
        self.assertEqual(
            Booking.objects.filter(status=Booking.Status.COMPLETED).count(),
            1,
        )
