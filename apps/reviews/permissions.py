from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReviewPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.method in SAFE_METHODS:
            return True

        return obj.booking.renter_id == request.user.id
