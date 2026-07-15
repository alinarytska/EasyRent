from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.listings.models import Listing
from apps.reviews.models import Review
from apps.search_history.models import SearchHistory
from apps.users.models import User
from apps.view_history.models import ViewHistory


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

    def create_booking(self, listing, **overrides):
        data = {
            "listing": listing,
            "renter": self.renter,
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 4),
            "price_per_night": Decimal("120.00"),
            "total_price": Decimal("360.00"),
            "status": Booking.Status.PENDING,
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def test_landlord_can_create_listing(self):
        self.client.force_authenticate(user=self.landlord)

        response = self.client.post(
            "/api/v1/listings/",
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
            "/api/v1/listings/",
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
            "/api/v1/listings/",
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
            "/api/v1/listings/",
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
            f"/api/v1/listings/{listing.id}/",
            data={"title": "Updated apartment"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated apartment")

        listing.refresh_from_db()

        self.assertEqual(listing.title, "Updated apartment")

    def test_owner_cannot_update_listing_with_invalid_price(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"price_per_night": "0.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price_per_night", response.data)

        listing.refresh_from_db()

        self.assertEqual(listing.price_per_night, Decimal("120.00"))

    def test_owner_cannot_update_listing_with_invalid_rooms_count(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"rooms": 0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rooms", response.data)

        listing.refresh_from_db()

        self.assertEqual(listing.rooms, 2)

    def test_owner_cannot_update_listing_with_too_many_rooms(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"rooms": 51},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rooms", response.data)

        listing.refresh_from_db()

        self.assertEqual(listing.rooms, 2)

    def test_owner_cannot_update_listing_with_invalid_postal_code(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"postal_code": "1234"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("postal_code", response.data)

        listing.refresh_from_db()

        self.assertEqual(listing.postal_code, "10115")

    def test_owner_cannot_update_listing_with_invalid_property_type(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"property_type": "castle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("property_type", response.data)

        listing.refresh_from_db()

        self.assertEqual(listing.property_type, Listing.PropertyType.APARTMENT)

    def test_owner_cannot_change_listing_owner(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"owner": self.other_landlord.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        listing.refresh_from_db()

        self.assertEqual(listing.owner, self.landlord)

    def test_owner_cannot_deactivate_listing_with_pending_booking(self):
        listing = self.create_listing(owner=self.landlord)
        self.create_booking(listing=listing, status=Booking.Status.PENDING)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_active", response.data)

        listing.refresh_from_db()

        self.assertTrue(listing.is_active)

    def test_owner_cannot_deactivate_listing_with_confirmed_booking(self):
        listing = self.create_listing(owner=self.landlord)
        self.create_booking(listing=listing, status=Booking.Status.CONFIRMED)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_active", response.data)

        listing.refresh_from_db()

        self.assertTrue(listing.is_active)

    def test_owner_can_deactivate_listing_with_closed_bookings(self):
        listing = self.create_listing(owner=self.landlord)
        self.create_booking(
            listing=listing,
            status=Booking.Status.CANCELLED,
        )
        self.create_booking(
            listing=listing,
            start_date=date(2026, 8, 5),
            end_date=date(2026, 8, 8),
            status=Booking.Status.COMPLETED,
        )
        self.create_booking(
            listing=listing,
            start_date=date(2026, 8, 9),
            end_date=date(2026, 8, 12),
            status=Booking.Status.REJECTED,
        )
        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])

        listing.refresh_from_db()

        self.assertFalse(listing.is_active)

    def test_other_user_cannot_update_listing(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.other_landlord)

        response = self.client.patch(
            f"/api/v1/listings/{listing.id}/",
            data={"title": "Forbidden update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        listing.refresh_from_db()

        self.assertEqual(listing.title, "Apartment in Berlin")

    def test_owner_can_delete_own_listing(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.landlord)

        response = self.client.delete(f"/api/v1/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Listing.objects.filter(pk=listing.pk).exists())

    def test_owner_cannot_delete_listing_with_bookings(self):
        listing = self.create_listing(owner=self.landlord)
        booking = self.create_booking(
            listing=listing,
            status=Booking.Status.COMPLETED,
        )
        self.client.force_authenticate(user=self.landlord)

        response = self.client.delete(f"/api/v1/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertTrue(Listing.objects.filter(pk=listing.pk).exists())
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())

    def test_other_user_cannot_delete_listing(self):
        listing = self.create_listing(owner=self.landlord)
        self.client.force_authenticate(user=self.other_landlord)

        response = self.client.delete(f"/api/v1/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Listing.objects.filter(pk=listing.pk).exists())

    def test_listing_list_shows_only_active_listings(self):
        active_listing = self.create_listing(
            owner=self.landlord,
            title="Active apartment",
        )
        inactive_listing = self.create_listing(
            owner=self.landlord,
            title="Inactive apartment",
            is_active=False,
        )
        self.client.force_authenticate(user=self.renter)

        response = self.client.get("/api/v1/listings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(active_listing.id, listing_ids)
        self.assertNotIn(inactive_listing.id, listing_ids)

    def test_anonymous_user_can_view_active_listing_list(self):
        active_listing = self.create_listing(
            owner=self.landlord,
            title="Active apartment",
        )
        inactive_listing = self.create_listing(
            owner=self.landlord,
            title="Inactive apartment",
            is_active=False,
        )

        response = self.client.get("/api/v1/listings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(active_listing.id, listing_ids)
        self.assertNotIn(inactive_listing.id, listing_ids)

    def test_anonymous_user_can_retrieve_active_listing(self):
        listing = self.create_listing(owner=self.landlord)

        response = self.client.get(f"/api/v1/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], listing.id)

    def test_anonymous_user_cannot_retrieve_inactive_listing(self):
        listing = self.create_listing(
            owner=self.landlord,
            is_active=False,
        )

        response = self.client.get(f"/api/v1/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_user_cannot_view_my_listings(self):
        response = self.client.get("/api/v1/listings/my/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_see_inactive_listing_in_my_listings(self):
        inactive_listing = self.create_listing(
            owner=self.landlord,
            title="Inactive apartment",
            is_active=False,
        )
        other_inactive_listing = self.create_listing(
            owner=self.other_landlord,
            title="Other inactive apartment",
            is_active=False,
        )
        self.client.force_authenticate(user=self.landlord)

        response = self.client.get("/api/v1/listings/my/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(inactive_listing.id, listing_ids)
        self.assertNotIn(other_inactive_listing.id, listing_ids)

    def test_owner_can_retrieve_own_inactive_listing(self):
        listing = self.create_listing(
            owner=self.landlord,
            is_active=False,
        )
        self.client.force_authenticate(user=self.landlord)

        response = self.client.get(f"/api/v1/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])

    def test_other_user_cannot_retrieve_inactive_listing(self):
        listing = self.create_listing(
            owner=self.landlord,
            is_active=False,
        )
        self.client.force_authenticate(user=self.other_landlord)

        response = self.client.get(f"/api/v1/listings/{listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_popular_listings_show_only_active_listings(self):
        active_listing = self.create_listing(
            owner=self.landlord,
            title="Active apartment",
        )
        inactive_listing = self.create_listing(
            owner=self.landlord,
            title="Inactive apartment",
            is_active=False,
        )
        self.client.force_authenticate(user=self.renter)

        response = self.client.get("/api/v1/listings/popular/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listing_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(active_listing.id, listing_ids)
        self.assertNotIn(inactive_listing.id, listing_ids)


class ListingSearchHistoryAPITests(APITestCase):
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
        self.create_listing(
            title="Berlin apartment",
            city="Berlin",
            price_per_night=Decimal("120.00"),
        )
        self.create_listing(
            title="Hamburg apartment",
            city="Hamburg",
            price_per_night=Decimal("90.00"),
        )

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
        }
        data.update(overrides)
        return Listing.objects.create(**data)

    def test_listing_search_creates_search_history_entry(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get(
            (
                "/api/v1/listings/?search=Berlin&city=Berlin&min_price=100"
                "&ordering=price_per_night&page=1"
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SearchHistory.objects.count(), 1)

        search_history = SearchHistory.objects.get()

        self.assertEqual(search_history.user, self.viewer)
        self.assertEqual(search_history.query, "Berlin")
        self.assertEqual(
            search_history.search_filters,
            {
                "city": "Berlin",
                "min_price": "100",
            },
        )

    def test_listing_filter_without_search_does_not_create_search_history(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get("/api/v1/listings/?city=Berlin&min_price=100")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SearchHistory.objects.exists())

    def test_blank_listing_search_does_not_create_search_history(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get("/api/v1/listings/?search=+++")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SearchHistory.objects.exists())

    def test_anonymous_listing_search_does_not_create_search_history(self):
        response = self.client.get("/api/v1/listings/?search=Berlin")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SearchHistory.objects.exists())


class ListingViewHistoryAPITests(APITestCase):
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
        self.listing = self.create_listing()
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
        }
        data.update(overrides)
        return Listing.objects.create(**data)

    def test_listing_detail_creates_view_history_entry(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get(f"/api/v1/listings/{self.listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["views_count"], 1)
        self.assertTrue(
            ViewHistory.objects.filter(
                user=self.viewer,
                listing=self.listing,
            ).exists()
        )

    def test_repeated_listing_detail_view_updates_existing_entry(self):
        self.client.force_authenticate(user=self.viewer)

        first_response = self.client.get(f"/api/v1/listings/{self.listing.id}/")
        second_response = self.client.get(f"/api/v1/listings/{self.listing.id}/")

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewHistory.objects.count(), 1)
        self.assertEqual(second_response.data["views_count"], 1)

    def test_listing_list_does_not_create_view_history_entry(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get("/api/v1/listings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ViewHistory.objects.exists())

    def test_anonymous_listing_detail_does_not_create_view_history_entry(self):
        response = self.client.get(f"/api/v1/listings/{self.listing.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ViewHistory.objects.exists())


class ListingReviewAPITests(APITestCase):
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
        self.renter = User.objects.create_user(
            email="renter@example.com",
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
        }
        data.update(overrides)
        return Listing.objects.create(**data)

    def create_completed_booking(self, listing, **overrides):
        data = {
            "listing": listing,
            "renter": self.renter,
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 4),
            "price_per_night": Decimal("120.00"),
            "total_price": Decimal("360.00"),
            "status": Booking.Status.COMPLETED,
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    def test_listing_reviews_returns_reviews_for_selected_listing(self):
        booking = self.create_completed_booking(self.listing)
        review = Review.objects.create(
            booking=booking,
            rating=5,
            comment="Excellent apartment.",
        )
        other_booking = self.create_completed_booking(
            self.other_listing,
            start_date=date(2026, 8, 5),
            end_date=date(2026, 8, 8),
        )
        other_review = Review.objects.create(
            booking=other_booking,
            rating=3,
            comment="Good apartment.",
        )
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get(f"/api/v1/listings/{self.listing.id}/reviews/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(review.id, review_ids)
        self.assertNotIn(other_review.id, review_ids)

    def test_anonymous_user_can_view_listing_reviews(self):
        booking = self.create_completed_booking(self.listing)
        review = Review.objects.create(
            booking=booking,
            rating=5,
            comment="Excellent apartment.",
        )

        response = self.client.get(f"/api/v1/listings/{self.listing.id}/reviews/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(review.id, review_ids)

    def test_listing_reviews_endpoint_does_not_create_view_history(self):
        self.create_completed_booking(self.listing)
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get(f"/api/v1/listings/{self.listing.id}/reviews/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ViewHistory.objects.exists())
