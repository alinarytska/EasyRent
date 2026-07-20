from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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


class UserViewSet(viewsets.GenericViewSet):
    """API endpoints for user profile, registration and account self-service."""

    serializer_class = UserSerializer
    throttle_scope = None

    @extend_schema(
        methods=("GET",),
        summary="Retrieve current user",
        description="Return profile information for the authenticated user.",
        responses=UserSerializer,
    )
    @extend_schema(
        methods=("PATCH",),
        summary="Update current user",
        description="Partially update the authenticated user's profile.",
        request=UserProfileUpdateSerializer,
        responses=UserSerializer,
    )
    @extend_schema(
        methods=("DELETE",),
        summary="Deactivate current user",
        description="Soft-deactivate the authenticated user account.",
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
        summary="Add rental group",
        description="Add Renters or Landlords group to the authenticated user.",
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
        summary="Change password",
        description="Change the authenticated user's password after validating the old password.",
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
        summary="Reactivate account",
        description="Reactivate a recently deactivated account within the recovery period.",
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
        summary="Register user",
        description="Create a new user account using email and password.",
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
