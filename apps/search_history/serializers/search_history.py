from rest_framework import serializers

from apps.search_history.models import SearchHistory


class SearchHistorySerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

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
