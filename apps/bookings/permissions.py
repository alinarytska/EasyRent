from rest_framework.permissions import SAFE_METHODS, BasePermission


class BookingPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        if view.action == "create":
            return request.user.is_authenticated and request.user.can_rent

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.method in SAFE_METHODS:
            return True

        return obj.listing.owner_id == request.user.id
