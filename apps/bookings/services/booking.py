from django.core.exceptions import ValidationError


def calculate_booking_prices(listing, start_date, end_date):
    number_of_nights = (end_date - start_date).days

    if number_of_nights <= 0:
        raise ValidationError("End date must be after start date.")

    price_per_night = listing.price_per_night
    total_price = price_per_night * number_of_nights

    return price_per_night, total_price
