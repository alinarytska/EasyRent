from django.contrib.auth.models import Group
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


class UserRegistrationAPITests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_user_can_register(self):
        response = self.client.post(
            "/api/v1/users/register/",
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
            "/api/v1/users/register/",
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


class JWTAuthenticationAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="auth@example.com",
            password="StrongPassword123!",
            first_name="Anna",
            last_name="Smith",
        )

    def test_user_can_obtain_jwt_tokens_with_email_and_password(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "auth@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_can_refresh_access_token(self):
        token_response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "auth@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        response = self.client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": token_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_user_cannot_obtain_tokens_with_invalid_password(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "auth@example.com",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_user_can_logout_with_refresh_token(self):
        token_response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "auth@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        access_token = token_response.data["access"]
        refresh_token = token_response.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.post(
            "/api/v1/auth/logout/",
            data={"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logged_out_refresh_token_cannot_be_used_again(self):
        token_response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "auth@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        access_token = token_response.data["access"]
        refresh_token = token_response.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.client.post(
            "/api/v1/auth/logout/",
            data={"refresh": refresh_token},
            format="json",
        )
        self.client.credentials()

        response = self.client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_logout(self):
        response = self.client.post(
            "/api/v1/auth/logout/",
            data={"refresh": "token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_refresh_token(self):
        token_response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "auth@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        access_token = token_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.post(
            "/api/v1/auth/logout/",
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("refresh", response.data)


class CurrentUserAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
            phone_number="+491234567890",
        )

    def obtain_tokens(self, password="strong-test-password"):
        return self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "profile@example.com",
                "password": password,
            },
            format="json",
        )

    def test_user_can_get_current_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/users/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profile@example.com")
        self.assertEqual(response.data["first_name"], "Anna")
        self.assertEqual(response.data["last_name"], "Smith")

    def test_user_can_update_current_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            "/api/v1/users/me/",
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
        response = self.client.get("/api/v1/users/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_update_current_profile(self):
        response = self.client.patch(
            "/api/v1/users/me/",
            data={"first_name": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_deactivate_current_account(self):
        self.user.groups.add(
            Group.objects.get(name=User.RENTERS_GROUP),
            Group.objects.get(name=User.LANDLORDS_GROUP),
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.delete("/api/v1/users/me/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

        self.user.refresh_from_db()

        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.has_usable_password())
        self.assertFalse(self.user.groups.exists())

    def test_anonymous_user_cannot_deactivate_account(self):
        response = self.client.delete("/api/v1/users/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_deactivated_user_cannot_obtain_jwt_tokens(self):
        self.client.force_authenticate(user=self.user)

        self.client.delete("/api/v1/users/me/")
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "profile@example.com",
                "password": "strong-test-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_account_deactivation_blacklists_existing_refresh_token(self):
        token_response = self.client.post(
            "/api/v1/auth/token/",
            data={
                "email": "profile@example.com",
                "password": "strong-test-password",
            },
            format="json",
        )
        access_token = token_response.data["access"]
        refresh_token = token_response.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.delete("/api/v1/users/me/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.client.credentials()
        refresh_response = self.client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_change_current_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/users/me/change-password/",
            data={
                "old_password": "strong-test-password",
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

        self.user.refresh_from_db()

        self.assertFalse(self.user.check_password("strong-test-password"))
        self.assertTrue(self.user.check_password("NewStrongPassword123!"))

        self.client.force_authenticate(user=None)
        old_password_response = self.obtain_tokens()
        new_password_response = self.obtain_tokens(
            password="NewStrongPassword123!",
        )

        self.assertEqual(
            old_password_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(new_password_response.status_code, status.HTTP_200_OK)

    def test_change_password_requires_correct_old_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/users/me/change-password/",
            data={
                "old_password": "wrong-password",
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password("strong-test-password"))

    def test_change_password_requires_matching_passwords(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/users/me/change-password/",
            data={
                "old_password": "strong-test-password",
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "DifferentStrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password_confirm", response.data)

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password("strong-test-password"))

    def test_change_password_rejects_same_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/users/me/change-password/",
            data={
                "old_password": "strong-test-password",
                "new_password": "strong-test-password",
                "new_password_confirm": "strong-test-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password("strong-test-password"))

    def test_change_password_rejects_weak_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/users/me/change-password/",
            data={
                "old_password": "strong-test-password",
                "new_password": "123",
                "new_password_confirm": "123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password("strong-test-password"))

    def test_change_password_blacklists_existing_refresh_token(self):
        token_response = self.obtain_tokens()
        access_token = token_response.data["access"]
        refresh_token = token_response.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.post(
            "/api/v1/users/me/change-password/",
            data={
                "old_password": "strong-test-password",
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.client.credentials()
        refresh_response = self.client.post(
            "/api/v1/auth/token/refresh/",
            data={"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_anonymous_user_cannot_change_password(self):
        response = self.client.post(
            "/api/v1/users/me/change-password/",
            data={
                "old_password": "strong-test-password",
                "new_password": "NewStrongPassword123!",
                "new_password_confirm": "NewStrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CurrentUserGroupAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="groups@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )

    def test_user_can_add_renters_group(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/users/me/groups/",
            data={"group": User.RENTERS_GROUP},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rental_groups"], [User.RENTERS_GROUP])
        self.assertTrue(response.data["can_rent"])
        self.assertFalse(response.data["can_create_listing"])

    def test_user_can_add_landlords_group_without_losing_renters_group(self):
        self.client.force_authenticate(user=self.user)
        self.user.groups.add(Group.objects.get(name=User.RENTERS_GROUP))

        response = self.client.post(
            "/api/v1/users/me/groups/",
            data={"group": User.LANDLORDS_GROUP},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data["rental_groups"]),
            {
                User.RENTERS_GROUP,
                User.LANDLORDS_GROUP,
            },
        )
        self.assertTrue(response.data["can_rent"])
        self.assertTrue(response.data["can_create_listing"])

    def test_adding_existing_group_is_idempotent(self):
        self.client.force_authenticate(user=self.user)
        self.user.groups.add(Group.objects.get(name=User.RENTERS_GROUP))

        response = self.client.post(
            "/api/v1/users/me/groups/",
            data={"group": User.RENTERS_GROUP},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rental_groups"], [User.RENTERS_GROUP])
        self.assertEqual(
            self.user.groups.filter(name=User.RENTERS_GROUP).count(),
            1,
        )
        self.assertTrue(response.data["can_rent"])
        self.assertFalse(response.data["can_create_listing"])

    def test_user_cannot_add_unknown_group(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/users/me/groups/",
            data={"group": "Admins"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("group", response.data)

    def test_anonymous_user_cannot_add_group(self):
        response = self.client.post(
            "/api/v1/users/me/groups/",
            data={"group": User.RENTERS_GROUP},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_replace_groups_with_patch(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            "/api/v1/users/me/groups/",
            data={"groups": [User.RENTERS_GROUP]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
