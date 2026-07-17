from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    date_hierarchy = "date_joined"
    list_display = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "is_renter",
        "is_landlord",
        "is_staff",
        "is_active",
        "deactivated_at",
    )
    list_filter = (
        "groups",
        "is_staff",
        "is_superuser",
        "is_active",
        "deactivated_at",
    )
    search_fields = ("email", "first_name", "last_name", "phone_number")
    readonly_fields = BaseUserAdmin.readonly_fields + ("deactivated_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal information",
            {"fields": ("first_name", "last_name", "phone_number")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "deactivated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    @admin.display(boolean=True, description="Renter")
    def is_renter(self, obj):
        return obj.can_rent

    @admin.display(boolean=True, description="Landlord")
    def is_landlord(self, obj):
        return obj.can_create_listing
