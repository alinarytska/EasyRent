from django.db import models


class BookingQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=self.model.Status.PENDING)

    def confirmed(self):
        return self.filter(status=self.model.Status.CONFIRMED)

    def rejected(self):
        return self.filter(status=self.model.Status.REJECTED)

    def cancelled(self):
        return self.filter(status=self.model.Status.CANCELLED)

    def completed(self):
        return self.filter(status=self.model.Status.COMPLETED)

    def blocking(self):
        return self.filter(
            status__in=(
                self.model.Status.PENDING,
                self.model.Status.CONFIRMED,
            )
        )

    def overlapping(self, start_date, end_date):
        return self.filter(
            start_date__lt=end_date,
            end_date__gt=start_date,
        )

    def for_listing(self, listing):
        return self.filter(listing=listing)

    def for_renter(self, renter):
        return self.filter(renter=renter)


class BookingManager(models.Manager.from_queryset(BookingQuerySet)):
    pass
