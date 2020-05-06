"""
This module defines any custom forms used by this application.

https://docs.djangoproject.com/en/3.0/topics/forms/
"""

from django import forms
from django.forms import Form, ModelForm, SlugField, URLField, Textarea
from .models import Resource, LicenseCode, Faculty, Department, Agreement, Signature, DEFAULT_ALLOWED_TAGS
from .fields import GroupedModelChoiceField


# Base Class

class ModelFormSetLabelSuffix(ModelForm):
    """A ModelForm which overrides their label_suffix to the empty string"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


# Resources

class ResourceCreateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for creating Resources"""

    class Meta:
        model = Resource
        fields = ['name', 'slug', 'description']
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
        fields = ['name', 'slug', 'description']
        widgets = {
            'description': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


# License Codes

class LicenseCodesField(forms.CharField):
    """A subclass of CharField which splits each line of input"""
    widget = Textarea

    def __init__(self, *args, **kwargs):
        self.resource = kwargs.pop('resource')
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if not value:
            return []
        return list(filter(None, map(lambda x: x.strip(), value.splitlines())))

    def validate(self, value):
        super().validate(value)
        seen = []
        for code in value:
            if LicenseCode.objects.filter(resource=self.resource, code=code).exists():
                raise forms.ValidationError(
                    'Invalid code: %(code)s is already associated with this resource.',
                    code='duplicate_access_code_in_database',
                    params={'code': code},
                )
            if code in seen:
                raise forms.ValidationError(
                    'Invalid code: %(code)s is a duplicate license code.',
                    code='duplicate_access_code_in_input',
                    params={'code': code},
                )
            seen.append(code)


class LicenseCodeAddForm(Form):
    """A form for searching for Signatures"""
    def __init__(self, *args, **kwargs):
        self.resource = kwargs.pop('resource')
        super().__init__(*args, **kwargs)
        self.fields['codes'] = LicenseCodesField(resource=self.resource, label='', help_text='One line per code')


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

    def clean(self):
        super().clean()
        if self.cleaned_data['end'] is not None:
            if self.cleaned_data['start'] > self.cleaned_data['end']:
                self.add_error(None,
                               forms.ValidationError(
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

    sign = forms.BooleanField(label='I have read and accepted this agreement')
    department = GroupedModelChoiceField(
        label='Your Department',
        queryset=Department.objects.all(),
        choices_groupby='faculty'
    )

    class Meta:
        model = Signature
        fields = ['sign', 'department']
        labels = {'department': 'Your Department'}


class SignatureSearchForm(Form):
    """A form for searching for Signatures"""
    search = forms.CharField(label='', max_length=100, required=False)
