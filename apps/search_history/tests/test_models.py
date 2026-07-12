from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.search_history.models import SearchHistory
from apps.users.models import User


class SearchHistoryModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="renter@example.com",
            password="strong-test-password",
            first_name="John",
            last_name="Brown",
        )

    def test_search_history_stores_query_and_filters(self):
        entry = SearchHistory.objects.create(
            user=self.user,
            query="Berlin apartment",
            search_filters={
                "min_price": 80,
                "max_price": 150,
                "rooms": 2,
            },
        )

        self.assertEqual(entry.query, "Berlin apartment")
        self.assertEqual(entry.search_filters["rooms"], 2)
        self.assertEqual(self.user.search_history.get(), entry)

    def test_query_is_required(self):
        entry = SearchHistory(
            user=self.user,
            query="",
            search_filters={"city": "Berlin"},
        )

        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_search_filters_are_optional(self):
        entry = SearchHistory(
            user=self.user,
            query="Berlin apartment",
        )

        entry.full_clean()

        self.assertEqual(entry.search_filters, {})

    def test_filters_default_is_not_shared_between_entries(self):
        first_entry = SearchHistory(user=self.user, query="Berlin")
        second_entry = SearchHistory(user=self.user, query="Hamburg")

        first_entry.search_filters["city"] = "Berlin"

        self.assertEqual(second_entry.search_filters, {})

    def test_string_representation_uses_query(self):
        entry = SearchHistory(
            user=self.user,
            query="Berlin apartment",
        )

        self.assertEqual(str(entry), "Berlin apartment")
