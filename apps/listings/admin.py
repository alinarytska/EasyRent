from django.contrib import admin

from apps.listings.models import Listing, ListingImage


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


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = (
        "listing",
        "is_primary",
        "position",
        "uploaded_at",
    )
    list_select_related = ("listing",)
    list_filter = ("is_primary", "uploaded_at")
    search_fields = ("listing__title",)
    autocomplete_fields = ("listing",)
    readonly_fields = ("uploaded_at",)
