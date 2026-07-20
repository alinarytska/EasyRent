from datetime import timedelta
import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError as APIValidationError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


logger = logging.getLogger(__name__)
ACCOUNT_RECOVERY_PERIOD = timedelta(days=30)


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
    """Soft-deactivate a user account and blacklist outstanding JWT tokens."""

    with transaction.atomic():
        locked_user = type(user).objects.select_for_update().get(pk=user.pk)

        locked_user.is_active = False
        locked_user.deactivated_at = timezone.now()
        locked_user.save(update_fields=("is_active", "deactivated_at"))

        _blacklist_user_tokens(locked_user)

    logger.info("User account deactivated: user_id=%s", locked_user.pk)
    return locked_user


def reactivate_user_account(user):
    """Reactivate a deactivated user account within the recovery period."""

    with transaction.atomic():
        locked_user = type(user).objects.select_for_update().get(pk=user.pk)

        if locked_user.is_active:
            raise APIValidationError(
                {"non_field_errors": "Account is already active."}
            )

        if not locked_user.deactivated_at:
            raise APIValidationError(
                {"non_field_errors": "Account cannot be reactivated."}
            )

        recovery_deadline = (
            locked_user.deactivated_at + ACCOUNT_RECOVERY_PERIOD
        )

        if timezone.now() > recovery_deadline:
            raise APIValidationError(
                {
                    "non_field_errors": (
                        "Account recovery period has expired."
                    )
                }
            )

        locked_user.is_active = True
        locked_user.deactivated_at = None
        locked_user.save(update_fields=("is_active", "deactivated_at"))

    logger.info("User account reactivated: user_id=%s", locked_user.pk)
    return locked_user


def change_user_password(user, new_password):
    """Change a user's password and invalidate existing JWT refresh tokens."""

    with transaction.atomic():
        locked_user = type(user).objects.select_for_update().get(pk=user.pk)

        locked_user.set_password(new_password)
        locked_user.save(update_fields=("password",))

        _blacklist_user_tokens(locked_user)

    logger.info("User password changed: user_id=%s", locked_user.pk)
    return locked_user
