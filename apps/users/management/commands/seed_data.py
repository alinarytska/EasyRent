from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from random import choice, randint, sample

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from faker import Faker
from PIL import Image

from apps.bookings.models import Booking
from apps.listings.models import Listing, ListingImage
from apps.reviews.models import Review
from apps.search_history.models import SearchHistory
from apps.users.models import User
from apps.view_history.models import ViewHistory


SEED_EMAIL_DOMAIN = "easyrent.local"
SEED_PASSWORD = "Testpass123!"
MAX_ATTEMPTS_MULTIPLIER = 50
DEFAULT_LANDLORDS = 150
DEFAULT_RENTERS = 200
DEFAULT_BOTH_USERS = 50
DEFAULT_LISTINGS = 400
DEFAULT_BOOKINGS = 450
DEFAULT_IMAGES_PER_LISTING = 1
DEFAULT_REVIEWS = 400
DEFAULT_SEARCH_HISTORY_ENTRIES = 450
DEFAULT_VIEW_HISTORY_ENTRIES = 450

GERMAN_CITIES = (
    "Berlin",
    "Hamburg",
    "Munich",
    "Cologne",
    "Frankfurt",
    "Stuttgart",
    "Dusseldorf",
    "Leipzig",
    "Dortmund",
    "Essen",
)

SEARCH_QUERIES = (
    "berlin apartment",
    "studio near city center",
    "family house",
    "room with balcony",
    "pet friendly apartment",
    "short term rental",
    "quiet district apartment",
)


class Command(BaseCommand):
    help = "Seed database with demo EasyRent data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete previously generated seed data before creating new data.",
        )
        parser.add_argument("--landlords", type=int, default=DEFAULT_LANDLORDS)
        parser.add_argument("--renters", type=int, default=DEFAULT_RENTERS)
        parser.add_argument("--both", type=int, default=DEFAULT_BOTH_USERS)
        parser.add_argument("--listings", type=int, default=DEFAULT_LISTINGS)
        parser.add_argument("--bookings", type=int, default=DEFAULT_BOOKINGS)
        parser.add_argument(
            "--images-per-listing",
            type=int,
            default=DEFAULT_IMAGES_PER_LISTING,
        )
        parser.add_argument("--reviews", type=int, default=DEFAULT_REVIEWS)
        parser.add_argument(
            "--search-history",
            type=int,
            default=DEFAULT_SEARCH_HISTORY_ENTRIES,
        )
        parser.add_argument(
            "--view-history",
            type=int,
            default=DEFAULT_VIEW_HISTORY_ENTRIES,
        )

    def handle(self, *args, **options):
        self.fake = Faker()
        self.validate_options(options)

        if options["clear"]:
            self.clear_seed_data()

        renters_group, landlords_group = self.get_user_groups()

        landlords = self.create_users(
            count=options["landlords"],
            email_prefix="landlord",
            groups=[landlords_group],
        )
        renters = self.create_users(
            count=options["renters"],
            email_prefix="renter",
            groups=[renters_group],
        )
        both_users = self.create_users(
            count=options["both"],
            email_prefix="both",
            groups=[renters_group, landlords_group],
        )

        listing_owners = landlords + both_users
        booking_renters = renters + both_users

        listings = self.create_listings(
            owners=listing_owners,
            count=options["listings"],
            images_per_listing=options["images_per_listing"],
        )
        bookings = self.create_bookings(
            renters=booking_renters,
            listings=listings,
            count=options["bookings"],
            min_completed_count=options["reviews"],
        )
        reviews = self.create_reviews(
            bookings=bookings,
            count=options["reviews"],
        )
        search_entries = self.create_search_history(
            users=booking_renters,
            count=options["search_history"],
        )
        view_entries = self.create_view_history(
            users=booking_renters,
            listings=listings,
            count=options["view_history"],
        )
        image_entries = ListingImage.objects.filter(listing__in=listings).count()
        total_entries = (
            len(landlords)
            + len(renters)
            + len(both_users)
            + len(listings)
            + image_entries
            + len(bookings)
            + len(reviews)
            + search_entries
            + view_entries
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed data ready: "
                f"{len(landlords) + len(renters) + len(both_users)} users, "
                f"{len(listings)} listings, "
                f"{image_entries} listing images, "
                f"{len(bookings)} bookings, "
                f"{len(reviews)} reviews, "
                f"{search_entries} search history entries, "
                f"{view_entries} view history entries. "
                f"Total demo records: about {total_entries}."
            )
        )

    def validate_options(self, options):
        if options["landlords"] + options["both"] < 1:
            raise CommandError(
                "At least one landlord or both-role user is required."
            )
        if options["renters"] + options["both"] < 1:
            raise CommandError(
                "At least one renter or both-role user is required."
            )
        if options["listings"] < 1:
            raise CommandError("The --listings value must be greater than 0.")
        if options["bookings"] < 0:
            raise CommandError("The --bookings value cannot be negative.")
        if options["images_per_listing"] < 0:
            raise CommandError(
                "The --images-per-listing value cannot be negative."
            )
        if options["reviews"] < 0:
            raise CommandError(
                "The --reviews value cannot be negative."
            )
        if options["reviews"] > options["bookings"]:
            raise CommandError(
                "The --reviews value cannot be greater than --bookings."
            )
        if options["search_history"] < 0:
            raise CommandError(
                "The --search-history value cannot be negative."
            )
        if options["view_history"] < 0:
            raise CommandError(
                "The --view-history value cannot be negative."
            )

    def get_max_attempts(self, count):
        return max(count * MAX_ATTEMPTS_MULTIPLIER, 20)

    def raise_if_not_enough_created(self, created_count, requested_count, label):
        if created_count < requested_count:
            raise CommandError(
                f"Could not create requested {requested_count} {label}. "
                f"Created only {created_count}. Try lowering the requested "
                "amount or clearing seed data with --clear."
            )

    def get_user_groups(self):
        renters_group, _ = Group.objects.get_or_create(name=User.RENTERS_GROUP)
        landlords_group, _ = Group.objects.get_or_create(
            name=User.LANDLORDS_GROUP,
        )

        return renters_group, landlords_group

    def clear_seed_data(self):
        seed_user_ids = list(
            User.objects.filter(
                email__endswith=f"@{SEED_EMAIL_DOMAIN}"
            ).values_list("id", flat=True)
        )
        seed_listing_ids = list(
            Listing.objects.filter(
                owner_id__in=seed_user_ids
            ).values_list("id", flat=True)
        )
        seed_booking_ids = list(
            Booking.objects.filter(
                Q(renter_id__in=seed_user_ids)
                | Q(listing_id__in=seed_listing_ids)
            ).values_list("id", flat=True)
        )

        SearchHistory.objects.filter(user_id__in=seed_user_ids).delete()
        ViewHistory.objects.filter(user_id__in=seed_user_ids).delete()
        ViewHistory.objects.filter(listing_id__in=seed_listing_ids).delete()
        self.delete_listing_images(seed_listing_ids)
        Review.objects.filter(booking_id__in=seed_booking_ids).delete()
        Booking.objects.filter(id__in=seed_booking_ids).delete()
        Listing.objects.filter(id__in=seed_listing_ids).delete()
        User.objects.filter(id__in=seed_user_ids).delete()

    def delete_listing_images(self, seed_listing_ids):
        for listing_image in ListingImage.objects.filter(
            listing_id__in=seed_listing_ids
        ):
            if listing_image.image:
                listing_image.image.delete(save=False)
            listing_image.delete()

    def create_users(self, count, email_prefix, groups):
        users = []
        attempts = 0
        user_index = 1
        max_attempts = self.get_max_attempts(count)

        while len(users) < count and attempts < max_attempts:
            attempts += 1
            email = f"{email_prefix}_{user_index}@{SEED_EMAIL_DOMAIN}"
            user_index += 1

            try:
                with transaction.atomic():
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "first_name": self.fake.first_name(),
                            "last_name": self.fake.last_name(),
                            "phone_number": self.generate_phone_number(),
                        },
                    )

                    if created:
                        user.set_password(SEED_PASSWORD)
                        user.full_clean()
                        user.save(update_fields=("password",))

                    user.groups.set(groups)
                    users.append(user)
            except (IntegrityError, ValidationError):
                continue

        self.raise_if_not_enough_created(len(users), count, "users")

        return users

    def create_listings(self, owners, count, images_per_listing):
        listings = []
        attempts = 0
        max_attempts = self.get_max_attempts(count)

        while len(listings) < count and attempts < max_attempts:
            attempts += 1
            city = choice(GERMAN_CITIES)

            try:
                with transaction.atomic():
                    listing = Listing(
                        owner=choice(owners),
                        title=f"{choice(Listing.PropertyType.labels)} in {city}",
                        description=self.fake.paragraph(nb_sentences=5),
                        property_type=choice(Listing.PropertyType.values),
                        price_per_night=self.generate_price(),
                        rooms=randint(1, 8),
                        city=city,
                        district=self.fake.street_suffix(),
                        postal_code=str(randint(10000, 99999)),
                        street=self.fake.street_name(),
                        house_number=str(randint(1, 200)),
                        is_active=True,
                    )
                    listing.full_clean()
                    listing.save()

                    for position in range(images_per_listing):
                        self.create_listing_image(
                            listing=listing,
                            position=position,
                            is_primary=position == 0,
                        )

                    listings.append(listing)
            except (IntegrityError, ValidationError):
                continue

        self.raise_if_not_enough_created(len(listings), count, "listings")

        return listings

    def create_listing_image(self, listing, position, is_primary):
        image_file = self.generate_image_file()
        listing_image = ListingImage(
            listing=listing,
            is_primary=is_primary,
            position=position,
        )
        listing_image.image.save(
            f"listing-{listing.pk}-{position}.jpg",
            image_file,
            save=False,
        )
        listing_image.full_clean()
        listing_image.save()

    def create_bookings(self, renters, listings, count, min_completed_count):
        bookings = []
        attempts = 0
        max_attempts = self.get_max_attempts(count)

        while len(bookings) < count and attempts < max_attempts:
            attempts += 1
            listing = choice(listings)
            available_renters = [
                renter
                for renter in renters
                if renter.pk != listing.owner_id
            ]

            if not available_renters:
                continue

            status = self.generate_booking_status(
                completed_bookings_count=len(
                    [
                        booking
                        for booking in bookings
                        if booking.status == Booking.Status.COMPLETED
                    ]
                ),
                min_completed_count=min_completed_count,
            )
            start_date, end_date = self.generate_booking_dates(status)
            price_per_night = listing.price_per_night
            total_price = price_per_night * (end_date - start_date).days

            try:
                with transaction.atomic():
                    booking = Booking(
                        listing=listing,
                        renter=choice(available_renters),
                        start_date=start_date,
                        end_date=end_date,
                        price_per_night=price_per_night,
                        total_price=total_price,
                        status=status,
                    )
                    booking.full_clean()
                    booking.save()
                    bookings.append(booking)
            except (IntegrityError, ValidationError):
                continue

        self.raise_if_not_enough_created(len(bookings), count, "bookings")

        return bookings

    def create_reviews(self, bookings, count):
        completed_bookings = [
            booking
            for booking in bookings
            if booking.status == Booking.Status.COMPLETED
        ]

        if count > len(completed_bookings):
            raise CommandError(
                f"Could not create requested {count} reviews. "
                f"Only {len(completed_bookings)} completed bookings are available."
            )

        available_bookings = sample(completed_bookings, count)
        reviews = []
        attempts = 0
        max_attempts = self.get_max_attempts(count)

        while len(reviews) < count and attempts < max_attempts and available_bookings:
            attempts += 1

            try:
                with transaction.atomic():
                    review = Review(
                        booking=available_bookings.pop(),
                        rating=randint(1, 5),
                        comment=self.fake.paragraph(nb_sentences=3),
                    )
                    review.full_clean()
                    review.save()
                    reviews.append(review)
            except (IntegrityError, ValidationError):
                continue

        self.raise_if_not_enough_created(len(reviews), count, "reviews")

        return reviews

    def create_search_history(self, users, count):
        entries_count = 0
        attempts = 0
        max_attempts = self.get_max_attempts(count)

        while entries_count < count and attempts < max_attempts:
            attempts += 1

            try:
                with transaction.atomic():
                    entry = SearchHistory(
                        user=choice(users),
                        query=choice(SEARCH_QUERIES),
                        search_filters={
                            "city": choice(GERMAN_CITIES),
                            "rooms": randint(1, 4),
                            "max_price": randint(80, 350),
                        },
                    )
                    entry.full_clean()
                    entry.save()
                    entries_count += 1
            except (IntegrityError, ValidationError):
                continue

        self.raise_if_not_enough_created(
            entries_count,
            count,
            "search history entries",
        )

        return entries_count

    def create_view_history(self, users, listings, count):
        entries_count = 0
        attempts = 0
        max_attempts = self.get_max_attempts(count)

        while entries_count < count and attempts < max_attempts:
            attempts += 1

            try:
                with transaction.atomic():
                    _, created = ViewHistory.objects.update_or_create(
                        user=choice(users),
                        listing=choice(listings),
                        defaults={},
                    )

                    if created:
                        entries_count += 1
            except (IntegrityError, ValidationError):
                continue

        self.raise_if_not_enough_created(
            entries_count,
            count,
            "view history entries",
        )

        return entries_count

    def generate_price(self):
        return Decimal(randint(50, 350)).quantize(Decimal("0.01"))

    def generate_phone_number(self):
        return f"+49{randint(1000000000, 9999999999)}"

    def generate_booking_status(self, completed_bookings_count, min_completed_count):
        if completed_bookings_count < min_completed_count:
            return Booking.Status.COMPLETED

        statuses = (
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
            Booking.Status.CONFIRMED,
            Booking.Status.COMPLETED,
            Booking.Status.COMPLETED,
            Booking.Status.CANCELLED,
            Booking.Status.REJECTED,
        )

        return choice(statuses)

    def generate_booking_dates(self, status):
        nights = randint(1, 14)

        if status == Booking.Status.COMPLETED:
            end_date = timezone.localdate() - timedelta(days=randint(1, 90))
            start_date = end_date - timedelta(days=nights)
        else:
            start_date = timezone.localdate() + timedelta(days=randint(1, 90))
            end_date = start_date + timedelta(days=nights)

        return start_date, end_date

    def generate_image_file(self):
        image = Image.new(
            "RGB",
            (800, 600),
            color=(
                randint(80, 230),
                randint(80, 230),
                randint(80, 230),
            ),
        )
        image_buffer = BytesIO()
        image.save(image_buffer, format="JPEG", quality=85)

        return ContentFile(image_buffer.getvalue())
