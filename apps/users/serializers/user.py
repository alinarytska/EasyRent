from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.users.models import User
from apps.users.services import ACCOUNT_RECOVERY_PERIOD


class UserSerializer(serializers.ModelSerializer):
    """Public account serializer for the authenticated user's profile."""

    can_rent = serializers.BooleanField(
        read_only=True,
        help_text="Whether the user belongs to the Renters group.",
    )
    can_create_listing = serializers.BooleanField(
        read_only=True,
        help_text="Whether the user belongs to the Landlords group.",
    )
    rental_groups = serializers.SerializerMethodField(
        help_text="Rental-related Django groups assigned to the user.",
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "rental_groups",
            "can_rent",
            "can_create_listing",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "rental_groups",
            "can_rent",
            "can_create_listing",
            "date_joined",
        )
        extra_kwargs = {
            "email": {"help_text": "Unique email used for login."},
            "first_name": {"help_text": "User first name."},
            "last_name": {"help_text": "User last name."},
            "phone_number": {"help_text": "Optional phone number in international format."},
            "date_joined": {"help_text": "Date and time when the account was created."},
        }

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_rental_groups(self, obj):
        return list(
            obj.groups.filter(
                name__in=(
                    User.RENTERS_GROUP,
                    User.LANDLORDS_GROUP,
                )
            ).values_list("name", flat=True)
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user account."""

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Password for the new account.",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Password confirmation. Must match password.",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_number",
        )
        extra_kwargs = {
            "email": {"help_text": "Unique email used for login."},
            "first_name": {"help_text": "User first name."},
            "last_name": {"help_text": "User last name."},
            "phone_number": {"help_text": "Optional phone number in international format."},
        }

    def validate(self, attrs):
        password = attrs["password"]
        password_confirm = attrs["password_confirm"]

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        validate_password(password)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating the current user's profile."""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
        )
        extra_kwargs = {
            "first_name": {"help_text": "Updated first name."},
            "last_name": {"help_text": "Updated last name."},
            "phone_number": {"help_text": "Updated phone number in international format."},
        }


class UserPasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing the current user's password."""

    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Current password.",
    )
    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="New password.",
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="New password confirmation. Must match new_password.",
    )

    def validate(self, attrs):
        user = self.context["request"].user
        old_password = attrs["old_password"]
        new_password = attrs["new_password"]
        new_password_confirm = attrs["new_password_confirm"]

        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"old_password": "Old password is incorrect."}
            )

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        if old_password == new_password:
            raise serializers.ValidationError(
                {
                    "new_password": (
                        "New password must be different from old password."
                    )
                }
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"new_password": list(error.messages)}
            ) from error

        return attrs


class UserReactivationSerializer(serializers.Serializer):
    """Serializer for restoring a recently deactivated account."""

    email = serializers.EmailField(help_text="Email of the deactivated account.")
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Password of the deactivated account.",
    )

    def validate(self, attrs):
        normalized_email = User.objects.normalize_email(attrs["email"]).lower()
        password = attrs["password"]

        try:
            user = User.objects.get(email=normalized_email)
        except User.DoesNotExist as error:
            raise serializers.ValidationError(
                {"non_field_errors": "Invalid credentials."}
            ) from error

        if user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": "Account is already active."}
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"non_field_errors": "Invalid credentials."}
            )

        if not user.deactivated_at:
            raise serializers.ValidationError(
                {"non_field_errors": "Account cannot be reactivated."}
            )

        now = self.context.get("now", timezone.now())

        if now > user.deactivated_at + ACCOUNT_RECOVERY_PERIOD:
            raise serializers.ValidationError(
                {
                    "non_field_errors": (
                        "Account recovery period has expired."
                    )
                }
            )

        attrs["user"] = user
        return attrs


class UserGroupAddSerializer(serializers.Serializer):
    """Serializer for adding one rental group to the current user."""

    group = serializers.ChoiceField(
        choices=(
            User.RENTERS_GROUP,
            User.LANDLORDS_GROUP,
        ),
        help_text="Group to add to the current user: Renters or Landlords.",
    )

    def update(self, instance, validated_data):
        group_name = validated_data["group"]
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
        return instance

    def create(self, validated_data):
        raise NotImplementedError(
            "UserGroupAddSerializer only updates existing users."
        )
