from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


def _blacklist_user_tokens(user):
    outstanding_tokens = OutstandingToken.objects.filter(user=user)

    for outstanding_token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(token=outstanding_token)


def deactivate_user_account(user):
    with transaction.atomic():
        locked_user = type(user).objects.select_for_update().get(pk=user.pk)

        locked_user.groups.clear()
        locked_user.set_unusable_password()
        locked_user.is_active = False
        locked_user.save(update_fields=("password", "is_active"))

        _blacklist_user_tokens(locked_user)

    return locked_user
