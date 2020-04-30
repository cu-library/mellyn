"""
This module defines the models used by this application.

https://docs.djangoproject.com/en/3.0/topics/db/models/
"""

from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import RegexValidator
from guardian.mixins import GuardianUserMixin
from django_bleach.models import BleachField

DEFAULT_ALLOWED_TAGS = ['h3', 'p', 'a', 'abbr', 'cite', 'code',
                        'small', 'em', 'strong', 'sub', 'sup',
                        'u', 'ul', 'ol', 'li']


class GroupDescription(models.Model):
    """Descriptions and slugs for Django's built in groups"""
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    # This duplication makes class based views much easier to impliment.
    name = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(max_length=300, unique=True,
                            validators=[RegexValidator(regex="^create$",
                                                       message="The slug cannot be 'create'.",
                                                       inverse_match=True)],
                            help_text='URL-safe identifier for the group.')
    description = BleachField(blank=True,
                              allowed_tags=DEFAULT_ALLOWED_TAGS,
                              allowed_attributes={'a': ['href', 'title'], 'abbr': ['title'], 'acronym': ['title']},
                              allowed_protocols=['https', 'mailto'],
                              strip_tags=False,
                              strip_comments=True,
                              help_text=f'An HTML description of the group. '
                                        f'The following tags are allowed: { ", ".join(DEFAULT_ALLOWED_TAGS)}.')

    def get_absolute_url(self):
        """Returns the canonical URL for a Group Description"""
        return reverse('groupdescriptions_read', args=[self.slug])

    def __str__(self):
        """Returns the string representation of a Group Description"""
        return self.group.name

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """A custom save method which creates or gets the group with the provided name"""
        self.group, _ = Group.objects.get_or_create(name=self.name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pylint: disable=arguments-differ
        super().delete(*args, **kwargs)
        self.group.delete()


class User(GuardianUserMixin, AbstractUser):
    """
    A custom user which inherits behaviour from Django's built in User class.

    This is here as a placeholder in case we want to make changes in the future, as
    recommended in the docs:
    https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
    """
