from django.db import models


class ListingQuerySet(models.QuerySet):
    """Reusable queryset filters for listing visibility and ownership."""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def by_owner(self, owner):
        return self.filter(owner=owner)


class ListingManager(models.Manager.from_queryset(ListingQuerySet)):
    """Manager exposing listing-specific queryset helpers."""

    pass
