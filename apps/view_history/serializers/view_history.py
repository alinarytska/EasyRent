from rest_framework import serializers

from apps.listings.models import Listing
from apps.view_history.models import ViewHistory


class ViewHistorySerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.active())
    listing_title = serializers.CharField(source="listing.title", read_only=True)

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
