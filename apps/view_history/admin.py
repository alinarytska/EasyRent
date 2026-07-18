from django.contrib import admin

from apps.view_history.models import ViewHistory


@admin.register(ViewHistory)
class ViewHistoryAdmin(admin.ModelAdmin):
    """Read-only admin configuration for listing view history."""

    list_display = ("user", "listing", "viewed_at")
    list_select_related = ("user", "listing")
    list_filter = ("viewed_at",)
    search_fields = ("user__email", "listing__title")
    readonly_fields = ("user", "listing", "viewed_at")
    date_hierarchy = "viewed_at"

    def has_add_permission(self, request):
        return False
