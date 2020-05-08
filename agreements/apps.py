"""
This module defines the Django application configuration.

https://docs.djangoproject.com/en/3.0/ref/applications/#configuring-applications
"""

from django.apps import AppConfig
from django.db.models.signals import post_save


class AgreementsConfig(AppConfig):
    """The configuration for the Agreements app."""
    name = 'agreements'

    def ready(self):
        from .signals import warn_low_number_unassigned_licensecodes  # pylint: disable=import-outside-toplevel
        post_save.connect(warn_low_number_unassigned_licensecodes,
                          sender='agreements.LicenseCode',
                          dispatch_uid="warn_low_number_unassigned_licensecodes")
