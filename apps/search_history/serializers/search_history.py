from rest_framework import serializers

from apps.search_history.models import SearchHistory


class SearchHistorySerializer(serializers.ModelSerializer):
    """Read-only serializer for a user's saved search history."""

    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        help_text="ID of the user who made the search.",
    )
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
        help_text="Email of the user who made the search.",
    )

    class Meta:
        model = SearchHistory
        fields = (
            "id",
            "user",
            "user_email",
            "query",
            "search_filters",
            "created_at",
        )
        read_only_fields = ("id", "user", "user_email", "created_at")
        extra_kwargs = {
            "query": {"help_text": "Keyword query entered by the user."},
            "search_filters": {"help_text": "Additional filters used together with the keyword."},
        }


class PopularSearchQuerySerializer(serializers.Serializer):
    """Aggregated popular search query result."""

    query = serializers.CharField(help_text="Search keyword.")
    search_count = serializers.IntegerField(help_text="Number of times the keyword was searched.")
