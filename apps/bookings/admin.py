from django.contrib import admin

from apps.bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin configuration for inspecting booking records."""

    list_display = (
        "listing",
        "renter",
        "start_date",
        "end_date",
        "status",
        "total_price",
        "created_at",
    )
    list_select_related = ("listing", "renter")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("listing__title", "renter__email")
    autocomplete_fields = ("listing", "renter")
    readonly_fields = (
        "price_per_night",
        "total_price",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
