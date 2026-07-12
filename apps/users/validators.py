from django.core.validators import RegexValidator


phone_number_validator = RegexValidator(
    regex=r"^\+[1-9]\d{7,14}$",
    message=(
        "Enter the phone number in international format, "
        "for example +491234567890."
    ),
)
