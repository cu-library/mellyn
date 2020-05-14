"""
This module defines any custom forms used by this application.

https://docs.djangoproject.com/en/3.0/topics/forms/
"""

from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.forms import Form, ModelForm, \
                         SlugField, CharField, Textarea, CheckboxSelectMultiple, ModelMultipleChoiceField

from guardian.forms import GroupObjectPermissionsForm

from .models import User, GroupDescription, DEFAULT_ALLOWED_TAGS


# Base Class

class ModelFormSetLabelSuffix(ModelForm):
    """A ModelForm which overrides label_suffix to the empty string"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)


# Group Descriptions

class GroupDescriptionCreateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for creating a GroupDescription"""

    class Meta:
        model = GroupDescription
        fields = ['name', 'slug', 'description']
        help_texts = {
            'slug': 'URL-safe identifier for the group. It cannot be changed after the group is created.',
            'name': 'The name of the group. It cannot be changed after the group is created.'
        }
        widgets = {
            'description': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


class GroupDescriptionUpdateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for updating a GroupDescription"""

    name = CharField(required=False,
                     help_text='The name of the group. It has been set and cannot be changed.',
                     disabled=True)

    slug = SlugField(required=False,
                     help_text='URL-safe identifier for the group. It has been set and cannot be changed.',
                     disabled=True)

    class Meta:
        model = GroupDescription
        fields = ['name', 'slug', 'description']
        widgets = {
            'description': Textarea(attrs={
                'cols': 80, 'rows': 20, 'wrap': 'off',
                'data-allowed-tags': ','.join(DEFAULT_ALLOWED_TAGS)
            }),
        }


class PermissionsChoiceField(ModelMultipleChoiceField):
    """
    A custom ModelMultipleChoiceField for permissions which uses the name
    and drops 'description' from group description.
    """
    def label_from_instance(self, obj):
        return obj.name.replace('group description', 'group')


class GroupPermissionsForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for updating the permissions associated with a group"""

    permissions = PermissionsChoiceField(widget=CheckboxSelectMultiple,
                                         label='Global permissions associated with this group.',
                                         queryset=(
                                             Permission.objects
                                             .filter(
                                                 Q(content_type__app_label='agreements') |
                                                 Q(content_type__model='groupdescription')
                                             )
                                             .exclude(
                                                 Q(content_type__model__icontains='historical')
                                             ))
                                         )

    class Meta:
        model = Group
        fields = ['permissions']


class CustomGroupObjectPermissionsForm(GroupObjectPermissionsForm):
    """A custom ModelForm for updating the permissions associated with a group"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)

    def get_obj_perms_field_widget(self):
        return CheckboxSelectMultiple

    def get_obj_perms_field_choices(self):
        choices = super().get_obj_perms_field_choices()
        filtered_choices = []
        for codename, name in choices:
            if codename.startswith('delete_') or codename.startswith('add_'):
                continue
            if codename.startswith('view_'):
                filtered_choices.append((codename, name+" even if hidden"))
            else:
                filtered_choices.append((codename, name))
        return filtered_choices

    def clean_permissions(self):
        """Remove unused permissions on form submission"""
        permissions = self.cleaned_data['permissions']
        return [permission for permission in permissions
                if not (permission.startswith('delete_') or permission.startswith('add_'))]


class UserSearchForm(Form):
    """A form for searching for Users"""
    search = CharField(label='', max_length=100, required=False)


class UserUpdateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for updating users"""

    class Meta:
        model = User
        fields = ['groups']
        widgets = {
            'groups': CheckboxSelectMultiple
        }


class UserUberUpdateForm(ModelFormSetLabelSuffix):
    """A custom ModelForm for updating users with all fields enabled"""

    class Meta:
        model = User
        fields = '__all__'
        widgets = {
            'groups': CheckboxSelectMultiple
        }
