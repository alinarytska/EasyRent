from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.users.serializers import JWTLogoutSerializer


class JWTLogoutView(GenericAPIView):
    serializer_class = JWTLogoutSerializer

    @extend_schema(
        request=JWTLogoutSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
