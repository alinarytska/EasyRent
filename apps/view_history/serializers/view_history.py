from rest_framework import serializers

from apps.listings.models import Listing
from apps.view_history.models import ViewHistory


class ViewHistorySerializer(serializers.ModelSerializer):
    """Read-only serializer for listings viewed by the current user."""

    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        help_text="ID of the user who viewed the listing.",
    )
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
        help_text="Email of the user who viewed the listing.",
    )
    listing = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.active(),
        help_text="ID of the viewed listing.",
    )
    listing_title = serializers.CharField(
        source="listing.title",
        read_only=True,
        help_text="Title of the viewed listing.",
    )

    class Meta:
        model = ViewHistory
        fields = (
            "id",
            "user",
            "user_email",
            "listing",
            "listing_title",
            "viewed_at",
        )
        read_only_fields = ("id", "user", "user_email", "listing_title", "viewed_at")
