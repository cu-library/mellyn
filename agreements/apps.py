"""
This module defines the Django application configuration.

https://docs.djangoproject.com/en/3.0/ref/applications/#configuring-applications
"""

from django.apps import AppConfig


class AgreementsConfig(AppConfig):
    """The configuration for the Agreements app."""
    name = 'agreements'
