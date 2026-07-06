from django.contrib import admin

from apps.listings.models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "property_type",
        "price_per_night",
        "rooms",
        "city",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "property_type", "city")
    search_fields = ("title", "description", "city", "district")
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")
