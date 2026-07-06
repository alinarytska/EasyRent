from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.users.models import User


class BookingModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
            role=User.Role.LANDLORD,
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

    def build_booking(self, **overrides):
        data = {
            "listing": self.listing,
            "renter": self.renter,
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 4),
            "price_per_night": Decimal("120.00"),
            "total_price": Decimal("360.00"),
        }
        data.update(overrides)
        return Booking(**data)

    def test_booking_has_expected_defaults_and_relations(self):
        booking = self.build_booking()
        booking.full_clean()
        booking.save()

        self.assertEqual(booking.listing, self.listing)
        self.assertEqual(booking.renter, self.renter)
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.number_of_nights, 3)

    def test_end_date_must_be_after_start_date(self):
        booking = self.build_booking(
            start_date=date(2026, 8, 4),
            end_date=date(2026, 8, 4),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                booking.save()

    def test_price_snapshot_does_not_change_with_listing_price(self):
        booking = self.build_booking()
        booking.save()

        self.listing.price_per_night = Decimal("150.00")
        self.listing.save(update_fields=("price_per_night",))
        booking.refresh_from_db()

        self.assertEqual(booking.price_per_night, Decimal("120.00"))
        self.assertEqual(booking.total_price, Decimal("360.00"))

    def test_prices_must_be_greater_than_zero(self):
        booking = self.build_booking(
            price_per_night=Decimal("0.00"),
            total_price=Decimal("0.00"),
        )

        with self.assertRaises(ValidationError):
            booking.full_clean()
