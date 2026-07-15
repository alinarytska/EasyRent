def record_listing_view(user, listing):
    if not user.is_authenticated:
        return None

    from apps.view_history.models import ViewHistory

    view_history, _ = ViewHistory.objects.update_or_create(
        user=user,
        listing=listing,
        defaults={},
    )

    return view_history
