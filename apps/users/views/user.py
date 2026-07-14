from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.models import User
from apps.users.serializers import (
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.is_staff:
            return queryset

        return queryset.filter(pk=user.pk)

    @extend_schema(methods=("GET",), responses=UserSerializer)
    @extend_schema(
        methods=("PATCH",),
        request=UserProfileUpdateSerializer,
        responses=UserSerializer,
    )
    @action(detail=False, methods=("get", "patch"), url_path="me")
    def me(self, request):
        if request.method == "PATCH":
            serializer = UserProfileUpdateSerializer(
                request.user,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            response_serializer = self.get_serializer(user)
            return Response(response_serializer.data)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={status.HTTP_201_CREATED: UserSerializer},
    )
    @action(
        detail=False,
        methods=("post",),
        url_path="register",
        permission_classes=(AllowAny,),
    )
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = self.get_serializer(user)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )
