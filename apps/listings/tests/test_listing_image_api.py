from decimal import Decimal
import shutil
import tempfile

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.listings.models import Listing, ListingImage
from apps.users.models import User


class ListingImagePermissionAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp()
        cls._override_settings = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override_settings.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override_settings.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        self.owner.groups.add(
            Group.objects.get(name=User.LANDLORDS_GROUP),
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="strong-test-password",
            first_name="Bob",
            last_name="Green",
        )
        self.other_user.groups.add(
            Group.objects.get(name=User.LANDLORDS_GROUP),
        )
        self.listing = self.create_listing(owner=self.owner)
        self.other_listing = self.create_listing(
            owner=self.other_user,
            title="Other apartment",
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

    def create_uploaded_image(self, name="image.gif"):
        tiny_gif = (
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00"
            b"\x00\x00\x00\xff\xff\xff,\x00\x00\x00\x00"
            b"\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
        return SimpleUploadedFile(
            name,
            tiny_gif,
            content_type="image/gif",
        )

    def test_owner_can_add_image_to_own_listing(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/api/listings/images/",
            data={
                "listing": self.listing.id,
                "image": self.create_uploaded_image(),
                "position": 1,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["listing"], self.listing.id)
        self.assertEqual(response.data["listing_owner"], self.owner.id)
        self.assertEqual(self.listing.images.count(), 1)

    def test_anonymous_user_cannot_add_image(self):
        response = self.client.post(
            "/api/listings/images/",
            data={
                "listing": self.listing.id,
                "image": self.create_uploaded_image(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.listing.images.count(), 0)

    def test_other_user_cannot_add_image_to_listing(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            "/api/listings/images/",
            data={
                "listing": self.listing.id,
                "image": self.create_uploaded_image(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.listing.images.count(), 0)

    def test_owner_can_update_own_listing_image(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="test-image.jpg",
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/listings/images/{listing_image.id}/",
            data={"position": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["position"], 5)

        listing_image.refresh_from_db()

        self.assertEqual(listing_image.position, 5)

    def test_owner_cannot_add_second_primary_image_to_listing(self):
        ListingImage.objects.create(
            listing=self.listing,
            image="primary-image.jpg",
            is_primary=True,
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            "/api/listings/images/",
            data={
                "listing": self.listing.id,
                "image": self.create_uploaded_image(),
                "is_primary": True,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_primary", response.data)
        self.assertEqual(
            ListingImage.objects.filter(
                listing=self.listing,
                is_primary=True,
            ).count(),
            1,
        )

    def test_owner_cannot_mark_second_image_as_primary(self):
        ListingImage.objects.create(
            listing=self.listing,
            image="primary-image.jpg",
            is_primary=True,
        )
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="regular-image.jpg",
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/listings/images/{listing_image.id}/",
            data={"is_primary": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_primary", response.data)

        listing_image.refresh_from_db()

        self.assertFalse(listing_image.is_primary)

    def test_other_user_cannot_update_listing_image(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="test-image.jpg",
        )
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            f"/api/listings/images/{listing_image.id}/",
            data={"position": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        listing_image.refresh_from_db()

        self.assertEqual(listing_image.position, 0)

    def test_owner_cannot_move_image_to_another_listing(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="test-image.jpg",
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            f"/api/listings/images/{listing_image.id}/",
            data={"listing": self.other_listing.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("listing", response.data)

        listing_image.refresh_from_db()

        self.assertEqual(listing_image.listing, self.listing)

    def test_owner_can_delete_own_listing_image(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="test-image.jpg",
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(
            f"/api/listings/images/{listing_image.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ListingImage.objects.filter(pk=listing_image.pk).exists()
        )

    def test_other_user_cannot_delete_listing_image(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="test-image.jpg",
        )
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f"/api/listings/images/{listing_image.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            ListingImage.objects.filter(pk=listing_image.pk).exists()
        )

    def test_owner_can_view_image_for_inactive_listing(self):
        inactive_listing = self.create_listing(
            owner=self.owner,
            title="Inactive apartment",
            is_active=False,
        )
        listing_image = ListingImage.objects.create(
            listing=inactive_listing,
            image="test-image.jpg",
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(
            f"/api/listings/images/{listing_image.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["listing"], inactive_listing.id)

    def test_other_user_cannot_view_image_for_inactive_listing(self):
        inactive_listing = self.create_listing(
            owner=self.owner,
            title="Inactive apartment",
            is_active=False,
        )
        listing_image = ListingImage.objects.create(
            listing=inactive_listing,
            image="test-image.jpg",
        )
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            f"/api/listings/images/{listing_image.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_image_list_hides_inactive_listing_images_from_other_user(self):
        active_listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="active-image.jpg",
        )
        inactive_listing = self.create_listing(
            owner=self.owner,
            title="Inactive apartment",
            is_active=False,
        )
        inactive_listing_image = ListingImage.objects.create(
            listing=inactive_listing,
            image="inactive-image.jpg",
        )
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get("/api/listings/images/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        image_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(active_listing_image.id, image_ids)
        self.assertNotIn(inactive_listing_image.id, image_ids)
