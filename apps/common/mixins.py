from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response


class ProtectedDestroyMixin:
    """Return a clear API error when database protection blocks deletion."""

    protected_destroy_error_message = (
        "This object cannot be deleted because it is used by other records."
    )

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": self.protected_destroy_error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
