from rest_framework import status
from rest_framework.test import APITestCase

from apps.search_history.models import SearchHistory
from apps.users.models import User


class SearchHistoryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="renter@example.com",
            password="strong-test-password",
            first_name="Anna",
            last_name="Smith",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="strong-test-password",
            first_name="Bob",
            last_name="Green",
        )

    def test_user_can_create_search_history_entry(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/search-history/",
            data={
                "query": "Berlin apartment",
                "search_filters": {
                    "city": "Berlin",
                    "rooms": 2,
                    "max_price": 150,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(response.data["query"], "Berlin apartment")
        self.assertEqual(response.data["search_filters"]["city"], "Berlin")
        self.assertTrue(
            SearchHistory.objects.filter(
                user=self.user,
                query="Berlin apartment",
            ).exists()
        )

    def test_user_cannot_create_search_history_for_another_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/search-history/",
            data={
                "user": self.other_user.id,
                "query": "Hamburg apartment",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertFalse(
            SearchHistory.objects.filter(
                user=self.other_user,
                query="Hamburg apartment",
            ).exists()
        )

    def test_anonymous_user_cannot_create_search_history_entry(self):
        response = self.client.post(
            "/api/search-history/",
            data={"query": "Berlin apartment"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(SearchHistory.objects.exists())

    def test_user_sees_only_own_search_history_entries(self):
        own_entry = SearchHistory.objects.create(
            user=self.user,
            query="Berlin apartment",
        )
        other_entry = SearchHistory.objects.create(
            user=self.other_user,
            query="Munich apartment",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/search-history/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(own_entry.id, entry_ids)
        self.assertNotIn(other_entry.id, entry_ids)

    def test_user_can_filter_search_history_by_query(self):
        berlin_entry = SearchHistory.objects.create(
            user=self.user,
            query="Berlin apartment",
        )
        hamburg_entry = SearchHistory.objects.create(
            user=self.user,
            query="Hamburg apartment",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/search-history/?query=berlin")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(berlin_entry.id, entry_ids)
        self.assertNotIn(hamburg_entry.id, entry_ids)

    def test_popular_queries_are_ordered_by_search_count(self):
        SearchHistory.objects.create(user=self.user, query="Berlin apartment")
        SearchHistory.objects.create(user=self.user, query="Berlin apartment")
        SearchHistory.objects.create(
            user=self.other_user,
            query="Munich apartment",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/search-history/popular/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first_result = response.data["results"][0]
        self.assertEqual(first_result["query"], "Berlin apartment")
        self.assertEqual(first_result["search_count"], 2)
