from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.users.models import User


class BookingPermissionAPITests(APITestCase):
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
        self.renter.groups.add(
            Group.objects.get(name=User.RENTERS_GROUP),
        )
        self.user_without_renter_group = User.objects.create_user(
            email="regular@example.com",
            password="strong-test-password",
            first_name="Maria",
            last_name="Brown",
        )
        self.listing = self.create_listing(owner=self.landlord)

    def create_listing(self, owner, **overrides):
        data = {
            "owner": owner,
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

    def create_booking(self, renter=None, **overrides):
        data = {
            "listing": self.listing,
            "renter": renter or self.renter,
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 4),
            "price_per_night": Decimal("120.00"),
            "total_price": Decimal("360.00"),
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def build_booking_payload(self, **overrides):
        data = {
            "listing": self.listing.id,
            "start_date": "2026-08-01",
            "end_date": "2026-08-04",
        }
        data.update(overrides)
        return data

    def test_renter_can_create_booking(self):
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/bookings/",
            data=self.build_booking_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["renter"], self.renter.id)
        self.assertEqual(response.data["listing"], self.listing.id)
        self.assertEqual(response.data["price_per_night"], "120.00")
        self.assertEqual(response.data["total_price"], "360.00")

    def test_user_without_renter_group_cannot_create_booking(self):
        self.client.force_authenticate(user=self.user_without_renter_group)

        response = self.client.post(
            "/api/bookings/",
            data=self.build_booking_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Booking.objects.filter(renter=self.user_without_renter_group).exists()
        )

    def test_listing_owner_can_update_booking(self):
        booking = self.create_booking()
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/bookings/{booking.id}/",
            data={"end_date": "2026-08-05"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_price"], "480.00")

        booking.refresh_from_db()

        self.assertEqual(booking.end_date, date(2026, 8, 5))
        self.assertEqual(booking.total_price, Decimal("480.00"))

    def test_renter_cannot_update_booking_directly(self):
        booking = self.create_booking()
        self.client.force_authenticate(user=self.renter)

        response = self.client.patch(
            f"/api/bookings/{booking.id}/",
            data={"end_date": "2026-08-05"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        booking.refresh_from_db()

        self.assertEqual(booking.end_date, date(2026, 8, 4))
        self.assertEqual(booking.total_price, Decimal("360.00"))

    def test_listing_owner_can_delete_booking(self):
        booking = self.create_booking()
        self.client.force_authenticate(user=self.landlord)

        response = self.client.delete(f"/api/bookings/{booking.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(pk=booking.pk).exists())

    def test_renter_cannot_delete_booking_directly(self):
        booking = self.create_booking()
        self.client.force_authenticate(user=self.renter)

        response = self.client.delete(f"/api/bookings/{booking.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())
