"""
This module defines any custom forms used by this application.

https://docs.djangoproject.com/en/3.0/topics/forms/
"""

from django.forms import Form, ModelForm, BooleanField, CharField, SlugField, URLField, Textarea, ValidationError

from .models import Resource, Faculty, Department, Agreement, Signature, DEFAULT_ALLOWED_TAGS
from .fields import GroupedModelChoiceField, SplitLineField


# Base Class

class ModelFormSetLabelSuffix(ModelForm):
    """A ModelForm which overrides label_suffix to the empty string"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)


# Resources

class ResourceCreateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for creating Resources"""

    class Meta:
        model = Resource
        fields = ['name', 'slug', 'low_codes_threshold', 'low_codes_email', 'description', 'hidden']
        help_texts = {
            'slug': 'URL-safe identifier for the resource. It cannot be changed after the resource is created.'
        }
        widgets = {
            'description': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


class ResourceUpdateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for updating Resources"""

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the resource. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = Resource
        fields = ['name', 'slug', 'low_codes_threshold', 'low_codes_email', 'description', 'hidden']
        widgets = {
            'description': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


# License Codes

class LicenseCodeForm(Form):
    """A form for adding and updating License Codes"""
    codes = SplitLineField(label='', help_text='One line per code', required=False)


# Faculties

class FacultyCreateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for creating Faculties"""

    class Meta:
        model = Faculty
        fields = ['name', 'slug']
        help_texts = {
            'slug': 'URL-safe identifier for the faculty. It cannot be changed after the faculty is created.'
        }


class FacultyUpdateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for updating Faculties"""

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the faculty. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = Faculty
        fields = ['name', 'slug']


# Departments

class DepartmentCreateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for creating Departments"""

    class Meta:
        model = Department
        fields = ['name', 'slug', 'faculty']
        help_texts = {
            'slug': 'URL-safe identifier for the department. It cannot be changed after the department is created.'
        }


class DepartmentUpdateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for updating Departments"""

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the department. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = Department
        fields = ['name', 'slug', 'faculty']


# Agreements

class AgreementBaseForm(ModelFormSetLabelSuffix):
    """The base class of agreement forms"""

    class Meta:
        model = Agreement
        fields = []

    def clean(self):
        super().clean()
        if self.cleaned_data.get('end', None) is not None:
            if self.cleaned_data['start'] > self.cleaned_data['end']:
                self.add_error(None,
                               ValidationError(
                                   '"End" date and time is before "Start" date and time.',
                                   code='start_date_after_end_date',
                               ))


class AgreementCreateForm(AgreementBaseForm):
    """A custom ModelForm for creating Agreements"""

    redirect_url = URLField(help_text="URL where patrons will be redirected to after signing the agreement. "
                                      "It must start with 'https://'.",
                            initial='https://')

    class Meta:
        model = Agreement
        fields = ['title', 'slug', 'resource', 'start', 'end', 'body', 'hidden', 'redirect_url', 'redirect_text']
        help_texts = {
            'slug': 'URL-safe identifier for the Agreement. It cannot be changed after the Agreement is created.'
        }
        widgets = {
            'body': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


class AgreementUpdateForm(AgreementBaseForm):
    """A custom ModelForm for updating Departments"""

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the agreement. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = Agreement
        fields = ['title', 'slug', 'resource', 'start', 'end', 'body', 'hidden', 'redirect_url', 'redirect_text']
        widgets = {
            'body': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


# Signatures

class SignatureCreateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for Signatures"""

    sign = BooleanField(label='I have read and accepted this agreement')
    department = GroupedModelChoiceField(
        label='Your Department',
        queryset=Department.objects.all().order_by('faculty__name'),
        choices_groupby='faculty'
    )

    class Meta:
        model = Signature
        fields = ['sign', 'department']
        labels = {'department': 'Your Department'}


class SignatureSearchForm(Form):
    """A form for searching for Signatures"""
    search = CharField(label='', max_length=100, required=False)
