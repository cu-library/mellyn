"""
This module defines the Django application configuration.

https://docs.djangoproject.com/en/3.0/ref/applications/#configuring-applications
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """The configuration for the Accounts app."""
    name = 'accounts'
