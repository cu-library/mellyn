"""
This module defines the models used by this application.

https://docs.djangoproject.com/en/3.0/topics/db/models/
"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    A custom user which inherits behaviour from Django's built in User class.

    This is here as a placeholder in case we want to make changes in the future, as
    recommended in the docs:
    https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
    """
