from rest_framework.permissions import SAFE_METHODS, BasePermission


class ListingPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        if view.action == "create":
            return (
                request.user.is_authenticated
                and request.user.can_create_listing
            )

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.owner_id == request.user.id
