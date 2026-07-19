from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.models import User
from apps.users.serializers import (
    UserGroupAddSerializer,
    UserPasswordChangeSerializer,
    UserProfileUpdateSerializer,
    UserReactivationSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from apps.users.services import (
    change_user_password,
    deactivate_user_account,
    reactivate_user_account,
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    throttle_scope = None

    def get_queryset(self):
        queryset = User.objects.all()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(pk=user.pk)

    @extend_schema(methods=("GET",), responses=UserSerializer)
    @extend_schema(
        methods=("PATCH",),
        request=UserProfileUpdateSerializer,
        responses=UserSerializer,
    )
    @extend_schema(
        methods=("DELETE",),
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=("get", "patch", "delete"), url_path="me")
    def me(self, request):
        if request.method == "DELETE":
            deactivate_user_account(request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

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
        request=UserGroupAddSerializer,
        responses=UserSerializer,
    )
    @action(detail=False, methods=("post",), url_path="me/groups")
    def add_group(self, request):
        serializer = UserGroupAddSerializer(
            request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = self.get_serializer(user)
        return Response(response_serializer.data)

    @extend_schema(
        request=UserPasswordChangeSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=("post",), url_path="me/change-password")
    def change_password(self, request):
        serializer = UserPasswordChangeSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        change_user_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=UserReactivationSerializer,
        responses=UserSerializer,
    )
    @action(
        detail=False,
        methods=("post",),
        url_path="reactivate",
        permission_classes=(AllowAny,),
        throttle_scope="auth",
    )
    def reactivate(self, request):
        serializer = UserReactivationSerializer(
            data=request.data,
            context={"now": timezone.now()},
        )
        serializer.is_valid(raise_exception=True)
        user = reactivate_user_account(serializer.validated_data["user"])
        response_serializer = self.get_serializer(user)
        return Response(response_serializer.data)

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={status.HTTP_201_CREATED: UserSerializer},
    )
    @action(
        detail=False,
        methods=("post",),
        url_path="register",
        permission_classes=(AllowAny,),
        throttle_scope="registration",
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
