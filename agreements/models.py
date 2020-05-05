"""
This module defines the models used by this application.

https://docs.djangoproject.com/en/3.0/topics/db/models/
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator, URLValidator, validate_email
from django_bleach.models import BleachField
from simple_history.models import HistoricalRecords

DEFAULT_ALLOWED_TAGS = ['h3', 'p', 'a', 'abbr', 'cite', 'code',
                        'small', 'em', 'strong', 'sub', 'sup',
                        'u', 'ul', 'ol', 'li']


class Resource(models.Model):
    """Resources which are protected by Agreements"""
    name = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(max_length=300, unique=True,
                            validators=[RegexValidator(regex="^create$",
                                                       message="The slug cannot be 'create'.",
                                                       inverse_match=True)],
                            help_text='URL-safe identifier for the resource.')
    description = BleachField(blank=True,
                              allowed_tags=DEFAULT_ALLOWED_TAGS,
                              allowed_attributes={'a': ['href', 'title'], 'abbr': ['title'], 'acronym': ['title']},
                              allowed_protocols=['https', 'mailto'],
                              strip_tags=False,
                              strip_comments=True,
                              help_text=f'An HTML description of the resource. '
                                        f'The following tags are allowed: { ", ".join(DEFAULT_ALLOWED_TAGS)}.')
    history = HistoricalRecords()

    def get_absolute_url(self):
        """Returns the canonical URL for a Faculty"""
        return reverse('resources_read', args=[self.slug])

    def __str__(self):
        """Returns the string representation of a Faculty"""
        return self.name


class Faculty(models.Model):
    """Faculties of the University"""
    name = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(max_length=300, unique=True,
                            validators=[RegexValidator(regex="^create$",
                                                       message="The slug cannot be 'create'.",
                                                       inverse_match=True)],
                            help_text='URL-safe identifier for the faculty.')
    history = HistoricalRecords()

    def get_absolute_url(self):
        """Returns the canonical URL for a Faculty"""
        return reverse('faculties_read', args=[self.slug])

    def __str__(self):
        """Returns the string representation of a Faculty"""
        return self.name


class Department(models.Model):
    """Departments of the University, which group patrons. Departments are part of Facilties"""
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True,
                            validators=[RegexValidator(regex="^create$",
                                                       message="The slug cannot be 'create'.",
                                                       inverse_match=True)],
                            help_text='URL-safe identifier for the department.')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def get_absolute_url(self):
        """Returns the canonical URL for a Department"""
        return reverse('departments_read', args=[self.slug])

    def __str__(self):
        """Returns the string representation of a Faculty"""
        return self.name


class Agreement(models.Model):
    """Agreements are documents which are signed by patrons to access resources"""
    title = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(max_length=300, unique=True,
                            validators=[RegexValidator(regex="^create$",
                                                       message="The slug cannot be 'create'.",
                                                       inverse_match=True)],
                            help_text='URL-safe identifier for the agreement.')
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    created = models.DateField(auto_now_add=True)
    body = BleachField(allowed_tags=DEFAULT_ALLOWED_TAGS,
                       allowed_attributes={'a': ['href', 'title'], 'abbr': ['title'], 'acronym': ['title']},
                       allowed_protocols=['https', 'mailto'],
                       strip_tags=False,
                       strip_comments=True,
                       help_text='HTML content of the agreement. '
                                 f'The following tags are allowed: { ", ".join(DEFAULT_ALLOWED_TAGS)}. '
                                 'Changing this field after the agreement has been signed '
                                 'by patrons is strongly discouraged.')

    redirect_url = models.URLField(validators=[URLValidator(schemes=['https'],
                                                            message="Enter a valid URL. "
                                                                    "It must start with 'https://'.",
                                                            code='need_https')],
                                   help_text="URL where patrons will be redirected to "
                                             "after signing the agreement. It must start with 'https://'.")
    redirect_text = models.CharField(max_length=300, help_text='The text of the URL redirect link.')
    hidden = models.BooleanField(default=False,
                                 help_text='Hidden agreements do not appear in the list of active agreements.')
    history = HistoricalRecords()

    def get_absolute_url(self):
        """Returns the canonical URL for an Agreement"""
        return reverse('agreements_read', args=[self.slug])


class Signature(models.Model):
    """
    Signatures define information about who agreed to what on what data.

    A signature provides a user access to an Agreement's resources.
    """
    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, limit_choices_to={'hidden': False})
    signatory = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    username = models.CharField(max_length=300)
    first_name = models.CharField(max_length=300, blank=True)
    last_name = models.CharField(max_length=300, blank=True)
    email = models.CharField(max_length=200, validators=[validate_email])
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    signed_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['agreement', 'signatory'], name='unique_signature')
        ]


class LicenseCode(models.Model):
    """License Codes are provided to patrons after they sign an agreement."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    code = models.CharField(max_length=300)
    added = models.DateTimeField(auto_now_add=True)
    signature = models.OneToOneField(Signature, on_delete=models.SET_NULL,
                                     related_name='license_code', blank=True, null=True)
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['resource', 'code'], name='unique_codes_per_resource')
        ]
