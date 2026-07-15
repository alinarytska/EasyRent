from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.utils import timezone
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
        self.other_renter = User.objects.create_user(
            email="other-renter@example.com",
            password="strong-test-password",
            first_name="John",
            last_name="White",
        )
        self.other_renter.groups.add(
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

    def test_renter_cannot_create_booking_for_another_user(self):
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/bookings/",
            data=self.build_booking_payload(renter=self.other_renter.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["renter"], self.renter.id)
        self.assertFalse(
            Booking.objects.filter(
                renter=self.other_renter,
                listing=self.listing,
            ).exists()
        )

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

    def test_user_cannot_book_own_listing(self):
        own_listing = self.create_listing(
            owner=self.renter,
            title="Own apartment",
        )
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/bookings/",
            data=self.build_booking_payload(listing=own_listing.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("listing", response.data)
        self.assertFalse(
            Booking.objects.filter(
                listing=own_listing,
                renter=self.renter,
            ).exists()
        )

    def test_user_cannot_create_booking_in_the_past(self):
        past_start_date = timezone.localdate() - timedelta(days=2)
        past_end_date = timezone.localdate() - timedelta(days=1)
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/bookings/",
            data=self.build_booking_payload(
                start_date=past_start_date.isoformat(),
                end_date=past_end_date.isoformat(),
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_date", response.data)

    def test_user_cannot_create_overlapping_booking(self):
        self.create_booking(status=Booking.Status.CONFIRMED)
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/bookings/",
            data=self.build_booking_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Booking.objects.count(), 1)

    def test_unrelated_user_cannot_retrieve_booking(self):
        booking = self.create_booking()
        self.client.force_authenticate(user=self.other_renter)

        response = self.client.get(f"/api/bookings/{booking.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unrelated_user_does_not_see_booking_in_list(self):
        booking = self.create_booking()
        self.client.force_authenticate(user=self.other_renter)

        response = self.client.get("/api/bookings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking_ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(booking.id, booking_ids)

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

    def test_listing_owner_can_confirm_pending_booking(self):
        booking = self.create_booking(status=Booking.Status.PENDING)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.post(f"/api/bookings/{booking.id}/confirm/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.CONFIRMED)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_renter_cannot_confirm_booking(self):
        booking = self.create_booking(status=Booking.Status.PENDING)
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(f"/api/bookings/{booking.id}/confirm/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_confirm_requires_pending_booking(self):
        booking = self.create_booking(status=Booking.Status.CANCELLED)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.post(f"/api/bookings/{booking.id}/confirm/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_listing_owner_can_reject_pending_booking(self):
        booking = self.create_booking(status=Booking.Status.PENDING)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.post(f"/api/bookings/{booking.id}/reject/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.REJECTED)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.REJECTED)

    def test_renter_cannot_reject_booking(self):
        booking = self.create_booking(status=Booking.Status.PENDING)
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(f"/api/bookings/{booking.id}/reject/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_unrelated_user_cannot_cancel_booking(self):
        booking = self.create_booking(status=Booking.Status.PENDING)
        self.client.force_authenticate(user=self.other_renter)

        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_renter_can_cancel_own_pending_booking(self):
        booking = self.create_booking(status=Booking.Status.PENDING)
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.CANCELLED)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_renter_cannot_cancel_booking_too_late(self):
        booking = self.create_booking(
            status=Booking.Status.PENDING,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=3),
        )
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_listing_owner_can_cancel_booking(self):
        booking = self.create_booking(status=Booking.Status.CONFIRMED)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.CANCELLED)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_cancel_requires_pending_or_confirmed_booking(self):
        booking = self.create_booking(status=Booking.Status.COMPLETED)
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.COMPLETED)
