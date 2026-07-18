from rest_framework.permissions import SAFE_METHODS, BasePermission


class ListingPermission(BasePermission):
    """Allow public reads and restrict listing writes to owners/landlords."""

    def has_permission(self, request, view):
        if view.action == "my_listings":
            return request.user.is_authenticated

        if request.method in SAFE_METHODS:
            return True

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


class ListingImagePermission(BasePermission):
    """Restrict listing image changes to the owner of the related listing."""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.listing.owner_id == request.user.id
