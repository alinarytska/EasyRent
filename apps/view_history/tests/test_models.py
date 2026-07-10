from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.listings.models import Listing
from apps.users.models import User
from apps.view_history.models import ViewHistory


class ViewHistoryModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        cls.viewer = User.objects.create_user(
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

    def test_view_history_stores_user_and_listing(self):
        entry = ViewHistory.objects.create(
            user=self.viewer,
            listing=self.listing,
        )

        self.assertEqual(entry.user, self.viewer)
        self.assertEqual(entry.listing, self.listing)
        self.assertEqual(self.viewer.view_history.get(), entry)
        self.assertEqual(self.listing.view_history.get(), entry)

    def test_user_can_have_only_one_view_per_listing(self):
        ViewHistory.objects.create(user=self.viewer, listing=self.listing)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ViewHistory.objects.create(
                    user=self.viewer,
                    listing=self.listing,
                )

    def test_repeated_view_updates_viewed_at(self):
        entry = ViewHistory.objects.create(
            user=self.viewer,
            listing=self.listing,
        )
        previous_viewed_at = timezone.now() - timedelta(days=1)
        ViewHistory.objects.filter(pk=entry.pk).update(
            viewed_at=previous_viewed_at,
        )

        updated_entry, created = ViewHistory.objects.update_or_create(
            user=self.viewer,
            listing=self.listing,
            defaults={},
        )

        self.assertFalse(created)
        self.assertEqual(ViewHistory.objects.count(), 1)
        self.assertGreater(updated_entry.viewed_at, previous_viewed_at)

    def test_string_representation_contains_user_and_listing(self):
        entry = ViewHistory(user=self.viewer, listing=self.listing)

        self.assertIn(str(self.viewer), str(entry))
        self.assertIn(str(self.listing), str(entry))
