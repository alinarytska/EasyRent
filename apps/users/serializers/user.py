from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.users.models import User
from apps.users.services import ACCOUNT_RECOVERY_PERIOD


class UserSerializer(serializers.ModelSerializer):
    can_rent = serializers.BooleanField(read_only=True)
    can_create_listing = serializers.BooleanField(read_only=True)
    rental_groups = serializers.SerializerMethodField()

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
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
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
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
        )


class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
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
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
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
    group = serializers.ChoiceField(
        choices=(
            User.RENTERS_GROUP,
            User.LANDLORDS_GROUP,
        ),
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
