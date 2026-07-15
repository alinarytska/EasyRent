from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from apps.listings.models import Listing
from apps.users.models import User


TEST_THROTTLE_SETTINGS = {
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "listings": "2/min",
        "popular": "2/min",
    },
}


@override_settings(REST_FRAMEWORK=TEST_THROTTLE_SETTINGS)
class ListingThrottlingAPITests(APITestCase):
    def setUp(self):
        self.original_throttle_rates = ScopedRateThrottle.THROTTLE_RATES.copy()
        ScopedRateThrottle.THROTTLE_RATES = settings.REST_FRAMEWORK[
            "DEFAULT_THROTTLE_RATES"
        ]
        cache.clear()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="strong-test-password",
            first_name="Bob",
            last_name="Green",
        )
        Listing.objects.create(
            owner=self.owner,
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

    def tearDown(self):
        cache.clear()
        ScopedRateThrottle.THROTTLE_RATES = self.original_throttle_rates

    def test_listing_search_is_throttled(self):
        self.client.force_authenticate(user=self.viewer)

        for _ in range(2):
            response = self.client.get("/api/listings/?search=Berlin")

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/listings/?search=Berlin")

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
