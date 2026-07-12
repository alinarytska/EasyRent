from rest_framework import serializers

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    can_rent = serializers.BooleanField(read_only=True)
    can_create_listing = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "can_rent",
            "can_create_listing",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "can_rent",
            "can_create_listing",
            "date_joined",
        )
