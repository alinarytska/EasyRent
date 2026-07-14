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
