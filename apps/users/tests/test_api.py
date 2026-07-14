from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


class UserRegistrationAPITests(APITestCase):
    def test_user_can_register(self):
        response = self.client.post(
            "/api/users/register/",
            data={
                "email": "Renter@Example.COM",
                "password": "Very-Strong-Password-123!",
                "password_confirm": "Very-Strong-Password-123!",
                "first_name": "Anna",
                "last_name": "Smith",
                "phone_number": "+491234567890",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_confirm", response.data)

        user = User.objects.get(email="renter@example.com")

        self.assertTrue(user.check_password("Very-Strong-Password-123!"))
        self.assertEqual(user.first_name, "Anna")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.phone_number, "+491234567890")

    def test_registration_requires_matching_passwords(self):
        response = self.client.post(
            "/api/users/register/",
            data={
                "email": "renter@example.com",
                "password": "Very-Strong-Password-123!",
                "password_confirm": "Different-Strong-Password-123!",
                "first_name": "Anna",
                "last_name": "Smith",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)
        self.assertFalse(
            User.objects.filter(email="renter@example.com").exists(),
        )


class CurrentUserAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
            phone_number="+491234567890",
        )

    def test_user_can_get_current_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profile@example.com")
        self.assertEqual(response.data["first_name"], "Anna")
        self.assertEqual(response.data["last_name"], "Smith")

    def test_user_can_update_current_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            "/api/users/me/",
            data={
                "first_name": "Updated",
                "last_name": "User",
                "phone_number": "+491111111111",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profile@example.com")
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["last_name"], "User")
        self.assertEqual(response.data["phone_number"], "+491111111111")

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.phone_number, "+491111111111")

    def test_anonymous_user_cannot_get_current_profile(self):
        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_update_current_profile(self):
        response = self.client.patch(
            "/api/users/me/",
            data={"first_name": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
