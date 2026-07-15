from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.reviews.models import Review
from apps.users.models import User


class ReviewPermissionAPITests(APITestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        self.renter = User.objects.create_user(
            email="renter@example.com",
            password="strong-test-password",
            first_name="Bob",
            last_name="Green",
        )
        self.other_renter = User.objects.create_user(
            email="other-renter@example.com",
            password="strong-test-password",
            first_name="Maria",
            last_name="Brown",
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="strong-test-password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        self.listing = self.create_listing(owner=self.landlord)
        self.completed_booking = self.create_booking(
            renter=self.renter,
            status=Booking.Status.COMPLETED,
        )
        self.other_completed_booking = self.create_booking(
            renter=self.other_renter,
            start_date=date(2026, 8, 5),
            end_date=date(2026, 8, 8),
            status=Booking.Status.COMPLETED,
        )
        self.pending_booking = self.create_booking(
            renter=self.renter,
            start_date=date(2026, 8, 9),
            end_date=date(2026, 8, 12),
            status=Booking.Status.PENDING,
        )

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

    def create_booking(self, renter, **overrides):
        data = {
            "listing": self.listing,
            "renter": renter,
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 4),
            "price_per_night": Decimal("120.00"),
            "total_price": Decimal("360.00"),
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def create_review(self, booking=None, **overrides):
        data = {
            "booking": booking or self.completed_booking,
            "rating": 5,
            "comment": "Excellent apartment.",
        }
        data.update(overrides)
        return Review.objects.create(**data)

    def test_renter_can_create_review_for_own_completed_booking(self):
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/reviews/",
            data={
                "booking": self.completed_booking.id,
                "rating": 5,
                "comment": "Excellent apartment.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], self.renter.id)
        self.assertEqual(response.data["booking"], self.completed_booking.id)
        self.assertEqual(response.data["rating"], 5)

    def test_anonymous_user_cannot_create_review(self):
        response = self.client.post(
            "/api/reviews/",
            data={
                "booking": self.completed_booking.id,
                "rating": 5,
                "comment": "Excellent apartment.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(
            Review.objects.filter(booking=self.completed_booking).exists()
        )

    def test_user_cannot_create_review_for_another_users_booking(self):
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/reviews/",
            data={
                "booking": self.other_completed_booking.id,
                "rating": 5,
                "comment": "Excellent apartment.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("booking", response.data)

    def test_user_cannot_create_review_for_pending_booking(self):
        self.client.force_authenticate(user=self.renter)

        response = self.client.post(
            "/api/reviews/",
            data={
                "booking": self.pending_booking.id,
                "rating": 5,
                "comment": "Excellent apartment.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("booking", response.data)

    def test_unrelated_user_cannot_retrieve_review(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.other_renter)

        response = self.client.get(f"/api/reviews/{review.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unrelated_user_does_not_see_review_in_list(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.other_renter)

        response = self.client.get("/api/reviews/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review_ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(review.id, review_ids)

    def test_staff_user_does_not_get_special_review_access_in_api(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(f"/api/reviews/{review.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_author_can_update_own_review(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.renter)

        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            data={"rating": 4, "comment": "Updated review."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 4)
        self.assertEqual(response.data["comment"], "Updated review.")

        review.refresh_from_db()

        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, "Updated review.")

    def test_listing_owner_cannot_update_review(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            data={"rating": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        review.refresh_from_db()

        self.assertEqual(review.rating, 5)

    def test_other_renter_cannot_update_review(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.other_renter)

        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            data={"rating": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        review.refresh_from_db()

        self.assertEqual(review.rating, 5)

    def test_author_cannot_change_review_booking(self):
        review = self.create_review()
        another_completed_booking = self.create_booking(
            renter=self.renter,
            start_date=date(2026, 8, 13),
            end_date=date(2026, 8, 16),
            status=Booking.Status.COMPLETED,
        )
        self.client.force_authenticate(user=self.renter)

        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            data={"booking": another_completed_booking.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("booking", response.data)

        review.refresh_from_db()

        self.assertEqual(review.booking, self.completed_booking)

    def test_author_can_delete_own_review(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.renter)

        response = self.client.delete(f"/api/reviews/{review.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_listing_owner_cannot_delete_review(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.landlord)

        response = self.client.delete(f"/api/reviews/{review.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())

    def test_other_renter_cannot_delete_review(self):
        review = self.create_review()
        self.client.force_authenticate(user=self.other_renter)

        response = self.client.delete(f"/api/reviews/{review.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())
