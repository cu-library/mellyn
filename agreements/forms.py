"""
This module defines any custom forms used by this application.

https://docs.djangoproject.com/en/3.0/topics/forms/
"""

from django import forms
from django.forms import Form, ModelForm, SlugField, URLField, Textarea
from .models import Resource, Faculty, Department, Agreement, Signature, DEFAULT_ALLOWED_TAGS
from .fields import GroupedModelChoiceField


# Resources

class ResourceCreateForm(ModelForm):
    """A custom ModelForm for creating Resources"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

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


class ResourceUpdateForm(ModelForm):
    """A custom ModelForm for updating Resources"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

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


# Faculties

class FacultyCreateForm(ModelForm):
    """A custom ModelForm for creating Faculties"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

    class Meta:
        model = Faculty
        fields = ['name', 'slug']
        help_texts = {
            'slug': 'URL-safe identifier for the faculty. It cannot be changed after the faculty is created.'
        }


class FacultyUpdateForm(ModelForm):
    """A custom ModelForm for updating Faculties"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the faculty. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = Faculty
        fields = ['name', 'slug']


# Departments

class DepartmentCreateForm(ModelForm):
    """A custom ModelForm for creating Departments"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

    class Meta:
        model = Department
        fields = ['name', 'slug', 'faculty']
        help_texts = {
            'slug': 'URL-safe identifier for the department. It cannot be changed after the department is created.'
        }


class DepartmentUpdateForm(ModelForm):
    """A custom ModelForm for updating Departments"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the department. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = Department
        fields = ['name', 'slug', 'faculty']


# Agreements

class AgreementCreateForm(ModelForm):
    """A custom ModelForm for creating Agreements"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

    redirect_url = URLField(help_text="URL where patrons will be redirected to after signing the agreement. "
                                      "It must start with 'https://'.",
                            initial='https://')

    class Meta:
        model = Agreement
        fields = ['title', 'slug', 'resource', 'body', 'hidden', 'redirect_url', 'redirect_text']
        help_texts = {
            'slug': 'URL-safe identifier for the Agreement. It cannot be changed after the Agreement is created.'
        }
        widgets = {
            'body': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


class AgreementUpdateForm(ModelForm):
    """A custom ModelForm for updating Departments"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the agreement. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = Agreement
        fields = ['title', 'slug', 'resource', 'body', 'hidden', 'redirect_url', 'redirect_text']
        widgets = {
            'body': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


# Signatures

class SignatureCreateForm(ModelForm):
    """A custom ModelForm for Signatures"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

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
