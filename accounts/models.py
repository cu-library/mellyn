"""
This module defines the models used by this application.

https://docs.djangoproject.com/en/3.0/topics/db/models/
"""

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Prefetch
from django.db.models.query import QuerySet
from django.urls import reverse

from guardian.mixins import GuardianUserMixin
from django_bleach.models import BleachField
from simple_history.models import HistoricalRecords

DEFAULT_ALLOWED_TAGS = ['h3', 'p', 'a', 'abbr', 'cite', 'code',
                        'small', 'em', 'strong', 'sub', 'sup',
                        'u', 'ul', 'ol', 'li']


class GroupDescriptionQuerySet(QuerySet):
    """A custom queryset for GroupDescriptions"""

    def for_model_with_permissions(self, model):
        """Return group descriptions with permissions related to the model"""
        if model is None:
            raise TypeError('model cannot be none')

        permissions_prefetch = Prefetch('group__permissions',
                                        queryset=(Permission.objects
                                                  .filter(content_type__model=model)
                                                  .distinct()
                                                  .order_by('name')),
                                        to_attr='permissions_on_model')

        return (self
                .filter(group__permissions__content_type__model=model)
                .distinct()
                .prefetch_related(permissions_prefetch)
                .order_by('name'))


class GroupDescription(models.Model):
    """Descriptions and slugs for Django's built in groups"""
    group = models.OneToOneField(Group, on_delete=models.CASCADE, blank=True)
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
    history = HistoricalRecords()

    objects = GroupDescriptionQuerySet.as_manager()

    def get_absolute_url(self):
        """Returns the canonical URL for a Group Description"""
        return reverse('groupdescriptions_read', args=[self.slug])

    def __str__(self):
        """Returns the string representation of a Group Description"""
        return self.group.name

    def clean(self):
        """Create or get the group with the provided name"""
        self.group, _ = Group.objects.get_or_create(name=self.name)

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
