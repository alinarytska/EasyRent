from django.contrib import admin

from apps.search_history.models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "query", "created_at")
    list_select_related = ("user",)
    list_filter = ("created_at",)
    search_fields = ("user__email", "query")
    readonly_fields = ("user", "query", "search_filters", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
