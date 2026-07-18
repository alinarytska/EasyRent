from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for inspecting renter reviews."""

    list_display = (
        "booking",
        "author",
        "listing",
        "rating",
        "created_at",
    )
    list_select_related = (
        "booking__renter",
        "booking__listing",
    )
    list_filter = ("rating", "created_at")
    search_fields = (
        "booking__renter__email",
        "booking__listing__title",
        "comment",
    )
    readonly_fields = ("booking", "created_at", "updated_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
