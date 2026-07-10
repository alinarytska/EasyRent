from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.reviews.models import Review
from apps.users.models import User


class ReviewModelTests(TestCase):
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
        cls.booking = Booking.objects.create(
            listing=cls.listing,
            renter=cls.renter,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 4),
            price_per_night=Decimal("120.00"),
            total_price=Decimal("360.00"),
            status=Booking.Status.COMPLETED,
        )

    def test_review_has_expected_relations(self):
        review = Review.objects.create(
            booking=self.booking,
            rating=5,
            comment="Excellent apartment.",
        )

        self.assertEqual(review.author, self.renter)
        self.assertEqual(review.listing, self.listing)
        self.assertEqual(self.booking.review, review)

    def test_rating_must_be_between_one_and_five(self):
        for rating in (0, 6):
            with self.subTest(rating=rating):
                review = Review(
                    booking=self.booking,
                    rating=rating,
                    comment="Invalid rating.",
                )

                with self.assertRaises(ValidationError):
                    review.full_clean()

    def test_review_can_have_empty_comment(self):
        review = Review(
            booking=self.booking,
            rating=5,
            comment="",
        )

        review.full_clean()

    def test_booking_can_have_only_one_review(self):
        Review.objects.create(
            booking=self.booking,
            rating=5,
            comment="First review.",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    booking=self.booking,
                    rating=4,
                    comment="Second review.",
                )

    def test_string_representation_contains_author_and_listing(self):
        review = Review(
            booking=self.booking,
            rating=5,
            comment="Excellent apartment.",
        )

        self.assertIn(str(self.renter), str(review))
        self.assertIn(str(self.listing), str(review))
