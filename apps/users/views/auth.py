import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.serializers import JWTLogoutSerializer


logger = logging.getLogger(__name__)


class JWTTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth"


class JWTTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth_refresh"


class JWTLogoutView(GenericAPIView):
    serializer_class = JWTLogoutSerializer
    throttle_scope = "auth"

    @extend_schema(
        request=JWTLogoutSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("User logged out: user_id=%s", request.user.pk)

        return Response(status=status.HTTP_204_NO_CONTENT)
