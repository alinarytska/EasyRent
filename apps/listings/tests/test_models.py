from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.listings.models import Listing
from apps.users.models import User


class ListingModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
            role=User.Role.LANDLORD,
        )

    def build_listing(self, **overrides):
        data = {
            "owner": self.owner,
            "title": "Apartment in Berlin",
            "description": "Bright apartment near the city center.",
            "property_type": Listing.PropertyType.APARTMENT,
            "price_per_night": Decimal("120.00"),
            "rooms": 2,
            "city": "Berlin",
            "district": "Mitte",
            "postal_code": "10115",
            "street": "Invalidenstrasse",
            "house_number": "1",
        }
        data.update(overrides)
        return Listing(**data)

    def test_listing_can_be_saved_with_owner(self):
        listing = self.build_listing()
        listing.full_clean()
        listing.save()

        self.assertEqual(listing.owner, self.owner)
        self.assertEqual(listing.price_per_night, Decimal("120.00"))
        self.assertEqual(str(listing), "Apartment in Berlin")

    def test_listing_is_active_by_default(self):
        listing = self.build_listing()

        self.assertTrue(listing.is_active)

    def test_property_type_accepts_valid_choice(self):
        listing = self.build_listing(
            property_type=Listing.PropertyType.HOUSE,
        )

        listing.full_clean()

        self.assertEqual(
            listing.property_type,
            Listing.PropertyType.HOUSE,
        )

    def test_price_per_night_must_be_greater_than_zero(self):
        listing = self.build_listing(price_per_night=Decimal("0.00"))

        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_rooms_must_be_greater_than_zero(self):
        listing = self.build_listing(rooms=0)

        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_postal_code_must_contain_five_digits(self):
        listing = self.build_listing(postal_code="1011")

        with self.assertRaises(ValidationError):
            listing.full_clean()
