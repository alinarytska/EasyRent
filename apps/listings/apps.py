from django.apps import AppConfig


class ListingsConfig(AppConfig):
    """Application configuration for the listings app."""

    name = 'apps.listings'

    def ready(self):
        import apps.listings.signals  # noqa: F401
