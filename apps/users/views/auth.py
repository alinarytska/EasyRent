import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.serializers import JWTLogoutSerializer


logger = logging.getLogger(__name__)


class JWTTokenObtainPairView(TokenObtainPairView):
    """JWT login endpoint returning access and refresh tokens."""

    throttle_scope = "auth"

    @extend_schema(
        summary="Obtain JWT token pair",
        description="Authenticate with email and password and return access and refresh tokens.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class JWTTokenRefreshView(TokenRefreshView):
    """JWT refresh endpoint returning a new access token."""

    throttle_scope = "auth_refresh"

    @extend_schema(
        summary="Refresh JWT access token",
        description="Use a valid refresh token to obtain a new access token.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class JWTLogoutView(GenericAPIView):
    """JWT logout endpoint that blacklists a refresh token."""

    serializer_class = JWTLogoutSerializer
    throttle_scope = "auth"

    @extend_schema(
        summary="Logout user",
        description="Blacklist the provided refresh token so it cannot be reused.",
        request=JWTLogoutSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("User logged out: user_id=%s", request.user.pk)

        return Response(status=status.HTTP_204_NO_CONTENT)
