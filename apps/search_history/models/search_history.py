from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class SearchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_history",
    )
    query = models.CharField(
        _("query"),
        max_length=255,
        db_index=True,
    )
    search_filters = models.JSONField(
        _("search filters"),
        default=dict,
        blank=True,
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Search history entry")
        verbose_name_plural = _("Search history entries")

    def __str__(self):
        return self.query
