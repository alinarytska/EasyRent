from decimal import Decimal
from pathlib import Path
import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from apps.listings.models import Listing, ListingImage
from apps.listings.validators import MAX_LISTING_IMAGE_SIZE_BYTES
from apps.users.models import User


class ListingImageModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.mkdtemp()
        cls._override_settings = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override_settings.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override_settings.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
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

    def test_listing_image_stores_listing_and_file_name(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image="test-image.jpg",
        )

        self.assertEqual(listing_image.listing, self.listing)
        self.assertEqual(listing_image.image.name, "test-image.jpg")
        self.assertEqual(self.listing.images.get(), listing_image)

    def test_listing_image_is_not_primary_by_default(self):
        listing_image = ListingImage(
            listing=self.listing,
            image="test-image.jpg",
        )

        self.assertFalse(listing_image.is_primary)
        self.assertEqual(listing_image.position, 0)

    def test_listing_image_accepts_file_with_allowed_size(self):
        image = SimpleUploadedFile(
            "allowed.jpg",
            b"x" * MAX_LISTING_IMAGE_SIZE_BYTES,
            content_type="image/jpeg",
        )
        listing_image = ListingImage(
            listing=self.listing,
            image=image,
        )

        listing_image.full_clean()

    def test_listing_image_file_must_not_exceed_max_size(self):
        image = SimpleUploadedFile(
            "too-large.jpg",
            b"x" * (MAX_LISTING_IMAGE_SIZE_BYTES + 1),
            content_type="image/jpeg",
        )
        listing_image = ListingImage(
            listing=self.listing,
            image=image,
        )

        with self.assertRaises(ValidationError):
            listing_image.full_clean()

    def test_primary_image_is_ordered_first(self):
        last_image = ListingImage.objects.create(
            listing=self.listing,
            image="last.jpg",
            position=2,
        )
        second_image = ListingImage.objects.create(
            listing=self.listing,
            image="second.jpg",
            position=1,
        )
        primary_image = ListingImage.objects.create(
            listing=self.listing,
            image="primary.jpg",
            is_primary=True,
            position=3,
        )

        self.assertEqual(
            list(self.listing.images.all()),
            [primary_image, second_image, last_image],
        )

    def test_listing_can_have_only_one_primary_image(self):
        ListingImage.objects.create(
            listing=self.listing,
            image="primary.jpg",
            is_primary=True,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ListingImage.objects.create(
                    listing=self.listing,
                    image="another-primary.jpg",
                    is_primary=True,
                )

    def test_upload_path_contains_listing_id_and_unique_file_name(self):
        listing_image = ListingImage(listing=self.listing)
        image_field = ListingImage._meta.get_field("image")

        first_path = Path(
            image_field.generate_filename(listing_image, "photo.JPG"),
        )
        second_path = Path(
            image_field.generate_filename(listing_image, "photo.JPG"),
        )

        expected_directory = Path("listings") / str(self.listing.pk)
        self.assertEqual(first_path.parent, expected_directory)
        self.assertEqual(first_path.suffix, ".jpg")
        self.assertNotEqual(first_path, second_path)

    def test_string_representation_contains_listing(self):
        listing_image = ListingImage(
            listing=self.listing,
            image="test-image.jpg",
        )

        self.assertIn(str(self.listing), str(listing_image))

    def test_image_file_is_deleted_from_storage_when_record_is_deleted(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image=SimpleUploadedFile(
                "delete-me.jpg",
                b"old-image-content",
                content_type="image/jpeg",
            ),
        )
        image_path = Path(listing_image.image.path)

        self.assertTrue(image_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            listing_image.delete()

        self.assertFalse(image_path.exists())

    def test_old_image_file_is_deleted_from_storage_when_image_is_replaced(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image=SimpleUploadedFile(
                "old-image.jpg",
                b"old-image-content",
                content_type="image/jpeg",
            ),
        )
        old_image_path = Path(listing_image.image.path)

        self.assertTrue(old_image_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            listing_image.image = SimpleUploadedFile(
                "new-image.jpg",
                b"new-image-content",
                content_type="image/jpeg",
            )
            listing_image.save()

        listing_image.refresh_from_db()
        new_image_path = Path(listing_image.image.path)

        self.assertFalse(old_image_path.exists())
        self.assertTrue(new_image_path.exists())

    def test_image_file_is_deleted_when_listing_is_deleted(self):
        listing_image = ListingImage.objects.create(
            listing=self.listing,
            image=SimpleUploadedFile(
                "cascade-delete.jpg",
                b"image-content",
                content_type="image/jpeg",
            ),
        )
        image_path = Path(listing_image.image.path)

        self.assertTrue(image_path.exists())

        with self.captureOnCommitCallbacks(execute=True):
            self.listing.delete()

        self.assertFalse(image_path.exists())
