from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models.manager import UserManager
from apps.users.validators import phone_number_validator


class User(AbstractUser):
    class Role(models.TextChoices):
        RENTER = "renter", _("Renter")
        LANDLORD = "landlord", _("Landlord")

    username = None

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    phone_number = models.CharField(
        _("phone number"),
        max_length=16,
        blank=True,
        validators=[phone_number_validator],
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.RENTER,
        db_index=True,
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
