from decimal import Decimal

from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from apps.listings.models import Listing
from apps.users.models import User


class ListingPermissionAPITests(APITestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        self.landlord.groups.add(
            Group.objects.get(name=User.LANDLORDS_GROUP),
        )
        self.renter = User.objects.create_user(
            email="renter@example.com",
            password="strong-test-password",
            first_name="Bob",
            last_name="Green",
        )
        self.other_landlord = User.objects.create_user(
            email="other-landlord@example.com",
            password="strong-test-password",
            first_name="Maria",
            last_name="Brown",
        )
        self.other_landlord.groups.add(
            Group.objects.get(name=User.LANDLORDS_GROUP),
        )

    def build_listing_payload(self, **overrides):
        data = {
            "title": "Apartment in Berlin",
            "description": "Bright apartment near the city center.",
            "property_type": Listing.PropertyType.APARTMENT,
            "price_per_night": "120.00",
            "rooms": 2,
            "city": "Berlin",
            "district": "Mitte",
            "postal_code": "10115",
            "street": "Invalidenstrasse",
            "house_number": "1",
        }
        data.update(overrides)
        return data

    def create_listing(self, owner=None, **overrides):
        data = {
            "owner": owner or self.landlord,
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
        return Listing.objects.create(**data)

    def test_landlord_can_create_listing(self):
        self.client.force_authenticate(user=self.landlord)

        response = self.client.post(
            "/api/listings/",
            data=self.build_listing_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.landlord.id)
        self.assertTrue(
            Listing.objects.filter(
                owner=self.landlord,
                title="Apartment in Berlin",
            ).exists()
        )

    def test_anonymous_user_cannot_create_listing(self):
        response = self.client.post(
            "/api/listings/",
            data=self.build_listing_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(
            Listing.objects.filter(title="Apartment in Berlin").exists()
        )

    def test_landlord_cannot_create_listing_for_another_owner(self):
        self.client.force_authenticate(user=self.landlord)

        response = self.client.post(
            "/api/listings/",
            data=self.build_listing_payload(owner=self.other_landlord.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.landlord.id)
        self.assertFalse(
            Listing.objects.filter(owner=self.other_landlord).exists()
        )

    def test_user_without_landlord_group_cannot_create_listing(self):
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/listings/",
            data=self.build_listing_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Listing.objects.filter(title="Apartment in Berlin").exists()
        )

    def test_owner_can_update_own_listing(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/listings/{listing.id}/",
            data={"title": "Updated apartment"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated apartment")

        listing.refresh_from_db()

        self.assertEqual(listing.title, "Updated apartment")

    def test_other_user_cannot_update_listing(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.other_landlord)

        response = self.client.patch(
            f"/api/listings/{listing.id}/",
            data={"title": "Forbidden update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        listing.refresh_from_db()

        self.assertEqual(listing.title, "Apartment in Berlin")

    def test_owner_can_delete_own_listing(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.delete(f"/api/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Listing.objects.filter(pk=listing.pk).exists())

    def test_other_user_cannot_delete_listing(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.other_landlord)

        response = self.client.delete(f"/api/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Listing.objects.filter(pk=listing.pk).exists())
