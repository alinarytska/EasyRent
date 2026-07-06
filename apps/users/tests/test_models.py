from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.users.models import User


class UserManagerTests(TestCase):
    def test_create_user_uses_email_for_authentication(self):
        user = User.objects.create_user(
            email="Renter@Example.COM",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
            phone_number="+491234567890",
        )

        self.assertEqual(user.email, "renter@example.com")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.phone_number, "+491234567890")
        self.assertEqual(user.role, User.Role.RENTER)
        self.assertTrue(user.check_password("strong-test-password"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_raises_error(self):
        with self.assertRaisesMessage(
            ValueError,
            "The email address must be provided.",
        ):
            User.objects.create_user(
                email="",
                password="strong-test-password",
                first_name="Anna",
                last_name="Smith",
            )

    def test_create_superuser_sets_permission_flags(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="strong-test-password",
            first_name="Admin",
            last_name="User",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_phone_number_must_use_international_format(self):
        user = User(
            email="renter@example.com",
            first_name="Anna",
            last_name="Smith",
            phone_number="0123456789",
        )

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_multiple_users_can_have_no_phone_number(self):
        first_user = User.objects.create_user(
            email="first@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        second_user = User.objects.create_user(
            email="second@example.com",
            password="strong-test-password",
            first_name="John",
            last_name="Smith",
        )

        self.assertEqual(first_user.phone_number, "")
        self.assertEqual(second_user.phone_number, "")

    def test_multiple_users_can_share_phone_number(self):
        first_user = User.objects.create_user(
            email="first@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
            phone_number="+491234567890",
        )
        second_user = User.objects.create_user(
            email="second@example.com",
            password="strong-test-password",
            first_name="John",
            last_name="Smith",
            phone_number="+491234567890",
        )

        self.assertEqual(first_user.phone_number, second_user.phone_number)
