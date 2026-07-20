from rest_framework.permissions import SAFE_METHODS, BasePermission


class BookingPermission(BasePermission):
    """Allow renters to book/update and landlords to manage status actions."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        if view.action == "create":
            return request.user.is_authenticated and request.user.can_rent

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if view.action in ("confirm", "reject"):
            return obj.listing.owner_id == request.user.id

        if view.action == "cancel":
            return (
                obj.renter_id == request.user.id
                or obj.listing.owner_id == request.user.id
            )

        if view.action in ("update", "partial_update"):
            return obj.renter_id == request.user.id

        return False
