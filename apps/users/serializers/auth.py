from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


class JWTLogoutSerializer(serializers.Serializer):
    """Serializer for blacklisting a JWT refresh token during logout."""

    refresh = serializers.CharField(
        write_only=True,
        help_text="Refresh token that should be blacklisted.",
    )

    def validate_refresh(self, refresh):
        try:
            token = RefreshToken(refresh)
        except TokenError:
            raise serializers.ValidationError("Invalid refresh token.")

        return token

    def save(self, **kwargs):
        refresh_token = self.validated_data["refresh"]
        refresh_token.blacklist()
