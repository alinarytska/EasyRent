from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models.manager import UserManager
from apps.users.validators import phone_number_validator


class User(AbstractUser):
    """Custom user model that authenticates by email and uses Django groups."""

    RENTERS_GROUP = "Renters"
    LANDLORDS_GROUP = "Landlords"

    username = None

    email = models.EmailField(
        _("email address"),
        unique=True,
        help_text=_("Unique email address used for login."),
    )
    first_name = models.CharField(
        _("first name"),
        max_length=150,
        help_text=_("User's first name."),
    )
    last_name = models.CharField(
        _("last name"),
        max_length=150,
        help_text=_("User's last name."),
    )
    phone_number = models.CharField(
        _("phone number"),
        max_length=16,
        blank=True,
        validators=[phone_number_validator],
        help_text=_("Optional phone number in international format."),
    )
    deactivated_at = models.DateTimeField(
        _("deactivated at"),
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Date and time when the user account was deactivated."),
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        ordering = ("email",)
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.email

    def belongs_to_group(self, group_name):
        if not self.pk:
            return False

        return self.groups.filter(name=group_name).exists()

    @property
    def can_rent(self):
        return self.belongs_to_group(self.RENTERS_GROUP)

    @property
    def can_create_listing(self):
        return self.belongs_to_group(self.LANDLORDS_GROUP)
