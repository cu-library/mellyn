"""
This module defines the models used by this application.

https://docs.djangoproject.com/en/3.0/topics/db/models/
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator, URLValidator, MaxValueValidator, MinValueValidator, \
                                   validate_email
from django_bleach.models import BleachField


class Agreement(models.Model):
    """Agreements are documents which are signed by patrons to access resources"""

    BODY_ALLOWED_TAGS = ['h3', 'p', 'a', 'abbr', 'cite', 'code',
                         'small', 'em', 'strong', 'sub', 'sup',
                         'u', 'ul', 'ol', 'li']

    title = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(max_length=300, unique=True,
                            validators=[RegexValidator(regex="^create$",
                                                       message="The slug cannot be 'create'.",
                                                       inverse_match=True)],
                            help_text='URL-safe identifier for the agreement. '
                                      'It cannot be changed after the agreement is created.')
    resource = models.CharField(max_length=300, help_text='What signing this agreement would give a patron access to.')
    resource_slug = models.SlugField(max_length=300, unique=True,
                                     help_text='URL-safe identifier for the resource. '
                                               'It cannot be changed after the agreement is created.')
    body = BleachField(allowed_tags=BODY_ALLOWED_TAGS,
                       allowed_attributes={'a': ['href', 'title'], 'abbr': ['title'], 'acronym': ['title']},
                       allowed_protocols=['https', 'mailto'],
                       strip_tags=False,
                       strip_comments=True,
                       help_text=f'HTML content of the Agreement. '
                                 f'The following tags are allowed: { ", ".join(BODY_ALLOWED_TAGS)}.')

    created = models.DateField(auto_now=True)
    hidden = models.BooleanField(default=False,
                                 help_text='Hidden agreements do not appear in the list of active agreements.')
    redirect_url = models.URLField(validators=[URLValidator(schemes=['https'],
                                                            message="Enter a valid URL. "
                                                                    "It must start with 'https://'.",
                                                            code='need_https')],
                                   help_text="URL where patrons will be redirected to "
                                             "after signing the agreement. It must start with 'https://'.")
    redirect_text = models.CharField(max_length=300, help_text='The text of the URL redirect link.')

    def get_absolute_url(self):
        """Returns the canonical URL for an Agreement"""
        return reverse('agreements_read', args=[self.slug])


class Faculty(models.Model):
    """Faculties of the University"""
    name = models.CharField(max_length=300, unique=True)
    slug = models.SlugField(max_length=300, unique=True,
                            validators=[RegexValidator(regex="^create$",
                                                       message="The slug cannot be 'create'.",
                                                       inverse_match=True)],
                            help_text='URL-safe identifier for the faculty. '
                                      'It cannot be changed after the Faculty is created.')

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
                            help_text='URL-safe identifier for the department. '
                                      'It cannot be changed after the Department is created.')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def get_absolute_url(self):
        """Returns the canonical URL for a Department"""
        return reverse('departments_read', args=[self.slug])


class Signature(models.Model):
    """
    Signatures define information about who agreed to what on what data.

    A signature provides a user access to an Agreement's resources.
    """

    BANNER_ID_OUT_OF_RANGE_ERROR_MESSAGE = 'Incorrect Banner ID Number'

    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE, limit_choices_to={'hidden': False})
    signatory = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=300)
    last_name = models.CharField(max_length=300)
    user_type = models.CharField(max_length=100)
    email = models.CharField(max_length=200, validators=[validate_email])
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    banner_id = models.IntegerField(validators=[MinValueValidator(100000000, BANNER_ID_OUT_OF_RANGE_ERROR_MESSAGE),
                                                MaxValueValidator(199999999, BANNER_ID_OUT_OF_RANGE_ERROR_MESSAGE)])
    signed_at = models.TimeField(auto_now_add=True)
