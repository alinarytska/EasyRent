from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle


TEST_THROTTLE_SETTINGS = {
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "2/min",
        "auth_refresh": "2/min",
        "registration": "1/min",
    },
}


@override_settings(REST_FRAMEWORK=TEST_THROTTLE_SETTINGS)
class AuthThrottlingAPITests(APITestCase):
    def setUp(self):
        self.original_throttle_rates = ScopedRateThrottle.THROTTLE_RATES.copy()
        ScopedRateThrottle.THROTTLE_RATES = settings.REST_FRAMEWORK[
            "DEFAULT_THROTTLE_RATES"
        ]
        cache.clear()

    def tearDown(self):
        cache.clear()
        ScopedRateThrottle.THROTTLE_RATES = self.original_throttle_rates

    def test_jwt_login_is_throttled(self):
        for _ in range(2):
            response = self.client.post(
                "/api/v1/auth/token/",
                data={
                    "email": "missing@example.com",
                    "password": "WrongPassword123!",
                },
                format="json",
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
            )

        response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "missing@example.com",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_registration_is_throttled(self):
        first_response = self.client.post(
            "/api/v1/users/register/",
            data={
                "email": "first@example.com",
                "password": "Very-Strong-Password-123!",
                "password_confirm": "Very-Strong-Password-123!",
                "first_name": "Anna",
                "last_name": "Smith",
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        second_response = self.client.post(
            "/api/v1/users/register/",
            data={
                "email": "second@example.com",
                "password": "Very-Strong-Password-123!",
                "password_confirm": "Very-Strong-Password-123!",
                "first_name": "Bob",
                "last_name": "Green",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
