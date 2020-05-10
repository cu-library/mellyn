"""
This module defines the models used by this application.

https://docs.djangoproject.com/en/3.0/topics/db/models/
"""

from datetime import timedelta

from django.conf import settings
from django.core.validators import RegexValidator, URLValidator, validate_email
from django.db import models
from django.db.models import Q, F, Count, Prefetch, UniqueConstraint, CheckConstraint
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.timezone import now

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
    low_codes_threshold = models.PositiveSmallIntegerField(default=51,
                                                           help_text='If the number of unassigned license codes '
                                                                     'associated with this resource falls below this '
                                                                     'threshold, start emailing warnings.')
    low_codes_email = models.CharField(blank=True,
                                       max_length=200,
                                       validators=[validate_email],
                                       help_text='The recipient of email warnings about low numbers of '
                                                 'remaning unassigned license codes.')
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

    class Meta:
        constraints = [
            UniqueConstraint(fields=['name', 'faculty'], name='%(app_label)s_%(class)s_unique_depts_in_faculty')
        ]

    def get_absolute_url(self):
        """Returns the canonical URL for a Department"""
        return reverse('departments_read', args=[self.slug])

    def __str__(self):
        """Returns the string representation of a Faculty"""
        return self.name


class AgreementQuerySet(QuerySet):
    """A custom queryset for Agreements"""

    def valid(self):
        """Filter out posts that aren't valid right now"""
        return (self
                .filter(start__lte=now())
                .filter(
                    Q(end__gte=now()) |
                    Q(end__isnull=True)
                )
                .exclude(hidden=True))

    def for_resource_with_signature(self, resource, signatory):
        """Return a list of agreements with the associated signature for a resource and user"""
        if resource is None:
            raise TypeError('resource cannot be none')
        if signatory is None:
            raise TypeError('signatory cannot be none')

        signature_prefetch = Prefetch('signature_set',
                                      queryset=Signature.objects.filter(signatory=signatory),
                                      to_attr='associated_signature_list')
        agreements = (self
                      .filter(resource=resource)
                      .prefetch_related(signature_prefetch)
                      .order_by('-created'))

        # Because of database constraints, the associated_signature_list will always be 0 or 1 elements long.
        for agreement in agreements:
            if len(agreement.associated_signature_list) > 0:
                agreement.associated_signature = agreement.associated_signature_list[0]

        return agreements


def date_121_days_from_now():
    """Return the current date plus approx one third of a year"""
    return now() + timedelta(days=121)


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
    start = models.DateTimeField(default=now,
                                 help_text='The agreement is valid starting at this date and time. '
                                           'Format (UTC timezone): YYYY-MM-DD HH:MM:SS')
    end = models.DateTimeField(null=True,
                               blank=True,
                               default=date_121_days_from_now,
                               help_text='The agreement is valid until this date and time. '
                                         'Format (UTC timezone): YYYY-MM-DD HH:MM:SS')
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

    objects = AgreementQuerySet.as_manager()

    class Meta:
        constraints = [
            CheckConstraint(check=Q(end__isnull=True) | Q(end__gt=F("start")),
                            name="%(app_label)s_%(class)s_end_null_or_gt_start")
        ]

    def get_absolute_url(self):
        """Returns the canonical URL for an Agreement"""
        return reverse('agreements_read', args=[self.slug])

    def valid(self):
        """Is this agreement not hidden, and currently valid?"""
        if not self.hidden:
            if now() >= self.start:
                if self.end is None:
                    return True
                if now() <= self.end:
                    return True
        return False


class SignatureQuerySet(QuerySet):
    """A custom queryset for Signatures"""

    def search(self, query):
        """Search signatures for the query"""
        if query is None:
            raise TypeError('query cannot be none')
        return self.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(department__name__icontains=query) |
            Q(department__faculty__name__icontains=query)
            )


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

    objects = SignatureQuerySet.as_manager()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['agreement', 'signatory'], name='%(app_label)s_%(class)s_unique_signature')
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
            UniqueConstraint(fields=['resource', 'code'], name='%(app_label)s_%(class)s_unique_codes_per_resource')
        ]


class FileDownloadEventQuerySet(QuerySet):
    """A custom queryset for FileDownloadEvents"""

    def get_or_create_if_no_duplicates_past_5_minutes(self, resource, accesspath, session_key):
        """Has a FileDownloadEvent for the same path and session been added in the past 5 minutes?"""
        if resource is None:
            raise TypeError('resource cannot be none')
        if accesspath is None:
            raise TypeError('accesspath cannot be none')
        if session_key is None:
            raise TypeError('session_key cannot be none')

        # Because the Unique Constraint on FileDownloadEvent doesn't enforce the time window
        # it might be possible that the same user might be able to add two events within the time window.
        return self.get_or_create(resource=resource,
                                  path=accesspath,
                                  session_key=session_key,
                                  at__gte=now()-timedelta(minutes=5))

    def download_count_per_path_for_resource(self, resource):
        """Group by and count on path for FileDownloadEvents"""
        if resource is None:
            raise TypeError('resource cannot be none')

        return (self
                .filter(resource=resource)
                .values('path')
                .annotate(downloads=Count('path'))
                .order_by('-downloads'))


class FileDownloadEvent(models.Model):
    """Store information about each file download request"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    path = models.CharField(max_length=300)
    session_key = models.CharField(max_length=50)
    at = models.DateTimeField(auto_now_add=True)

    objects = FileDownloadEventQuerySet.as_manager()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['resource', 'path', 'session_key', 'at'], name='%(app_label)s_%(class)s_unique')
        ]
