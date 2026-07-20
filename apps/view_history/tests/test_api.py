from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.listings.models import Listing
from apps.users.models import User
from apps.view_history.models import ViewHistory


class ViewHistoryAPITests(APITestCase):
    def setUp(self):
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
        self.other_viewer = User.objects.create_user(
            email="other-viewer@example.com",
            password="strong-test-password",
            first_name="Maria",
            last_name="Brown",
        )
        self.listing = self.create_listing(title="Berlin apartment")
        self.other_listing = self.create_listing(title="Hamburg apartment")

    def create_listing(self, **overrides):
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
            "is_active": True,
        }
        data.update(overrides)
        return Listing.objects.create(**data)

    def test_user_cannot_create_view_history_entry_manually(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.post(
            "/api/v1/view-history/",
            data={"listing": self.listing.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(ViewHistory.objects.exists())

    def test_user_cannot_update_view_history_entry_manually(self):
        entry = ViewHistory.objects.create(
            user=self.viewer,
            listing=self.listing,
        )
        self.client.force_authenticate(user=self.viewer)

        response = self.client.patch(
            f"/api/v1/view-history/{entry.id}/",
            data={"listing": self.other_listing.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(ViewHistory.objects.count(), 1)

        entry.refresh_from_db()

        self.assertEqual(entry.listing, self.listing)

    def test_user_cannot_create_view_history_for_another_user_manually(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.post(
            "/api/v1/view-history/",
            data={
                "user": self.other_viewer.id,
                "listing": self.listing.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(
            ViewHistory.objects.filter(
                user=self.other_viewer,
                listing=self.listing,
            ).exists()
        )

    def test_anonymous_user_cannot_create_view_history_entry(self):
        response = self.client.post(
            "/api/v1/view-history/",
            data={"listing": self.listing.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(ViewHistory.objects.exists())

    def test_user_sees_only_own_view_history_entries(self):
        own_entry = ViewHistory.objects.create(
            user=self.viewer,
            listing=self.listing,
        )
        other_entry = ViewHistory.objects.create(
            user=self.other_viewer,
            listing=self.other_listing,
        )
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get("/api/v1/view-history/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(own_entry.id, entry_ids)
        self.assertNotIn(other_entry.id, entry_ids)

    def test_user_can_filter_view_history_by_listing(self):
        own_entry = ViewHistory.objects.create(
            user=self.viewer,
            listing=self.listing,
        )
        other_entry = ViewHistory.objects.create(
            user=self.viewer,
            listing=self.other_listing,
        )
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get(
            f"/api/v1/view-history/?listing={self.listing.id}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(own_entry.id, entry_ids)
        self.assertNotIn(other_entry.id, entry_ids)
