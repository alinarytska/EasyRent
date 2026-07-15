from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.users.models import User


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
