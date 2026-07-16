import logging

from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


logger = logging.getLogger(__name__)


def _blacklist_user_tokens(user):
    outstanding_tokens = OutstandingToken.objects.filter(user=user)

    for outstanding_token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(token=outstanding_token)

    logger.info(
        "Outstanding tokens blacklisted for user_id=%s count=%s",
        user.pk,
        outstanding_tokens.count(),
    )


def deactivate_user_account(user):
    with transaction.atomic():
        locked_user = type(user).objects.select_for_update().get(pk=user.pk)

        locked_user.groups.clear()
        locked_user.set_unusable_password()
        locked_user.is_active = False
        locked_user.save(update_fields=("password", "is_active"))

        _blacklist_user_tokens(locked_user)

    logger.info("User account deactivated: user_id=%s", locked_user.pk)
    return locked_user


def change_user_password(user, new_password):
    with transaction.atomic():
        locked_user = type(user).objects.select_for_update().get(pk=user.pk)

        locked_user.set_password(new_password)
        locked_user.save(update_fields=("password",))

        _blacklist_user_tokens(locked_user)

    logger.info("User password changed: user_id=%s", locked_user.pk)
    return locked_user
