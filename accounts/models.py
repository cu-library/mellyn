"""
This module defines the models used by this application.

https://docs.djangoproject.com/en/3.0/topics/db/models/
"""

from django.contrib.auth.models import UserManager, AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Prefetch, Q
from django.db.models.query import QuerySet
from django.urls import reverse

from django_bleach.models import BleachField
from guardian.mixins import GuardianUserMixin
from guardian.models import GroupObjectPermission
from simple_history.models import HistoricalRecords

DEFAULT_ALLOWED_TAGS = ['h3', 'p', 'a', 'abbr', 'cite', 'code',
                        'small', 'em', 'strong', 'sub', 'sup',
                        'u', 'ul', 'ol', 'li']


class UserQuerySet(QuerySet):
    """A custom queryset for Users"""

    def search(self, query):
        """Search users for the query"""
        if query is None:
            raise TypeError('query cannot be none')
        return self.filter(
            Q(username__icontains=query) |   # pylint: disable=unsupported-binary-operation
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
            )


class CustomUserManager(UserManager):
    """A custom User model manager"""

    def get_queryset(self):
        """Return our custom User queryset"""
        return UserQuerySet(self.model, using=self._db)

    def search(self, query):
        """Wire the queryset and manager methods together"""
        return self.get_queryset().search(query)


class User(GuardianUserMixin, AbstractUser):
    """
    A custom user which inherits behaviour from Django's built in User class.

    This is here as a placeholder in case we want to make changes in the future, as
    recommended in the docs:
    https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
    """

    objects = CustomUserManager()


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

    def for_object_with_groupobjectpermissions(self, model, object_pk):
        """Return group descriptions with GroupObjectPermissions related to the object"""
        if model is None:
            raise TypeError('model cannot be none')
        if object_pk is None:
            raise TypeError('object_pk cannot be none')

        groupobjectpermission_prefetch = Prefetch('group__groupobjectpermission_set',
                                                  queryset=(GroupObjectPermission.objects
                                                            .filter(content_type__model=model, object_pk=object_pk)
                                                            .distinct()
                                                            .select_related('permission')),
                                                  to_attr='groupobjectpermissions_on_object')

        return (self
                .filter(group__groupobjectpermission__content_type__model=model,
                        group__groupobjectpermission__object_pk=object_pk)
                .distinct()
                .prefetch_related(groupobjectpermission_prefetch)
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
                                        f'The following tags are allowed: {", ".join(DEFAULT_ALLOWED_TAGS)}.')
    history = HistoricalRecords()

    objects = GroupDescriptionQuerySet.as_manager()

    def get_absolute_url(self):
        """Returns the canonical URL for a Group Description"""
        return reverse('groupdescriptions_read', args=[self.slug])

    def __str__(self):
        """Returns the string representation of a Group Description"""
        return self.group.name

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ,signature-differs
        """Create or get the group with the provided name"""
        self.group, _ = Group.objects.get_or_create(name=self.name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pylint: disable=arguments-differ,signature-differs
        super().delete(*args, **kwargs)
        self.group.delete()
