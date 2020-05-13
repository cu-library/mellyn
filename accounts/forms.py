"""
This module defines any custom forms used by this application.

https://docs.djangoproject.com/en/3.0/topics/forms/
"""

from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.forms import ModelForm, SlugField, CharField, Textarea, CheckboxSelectMultiple, ModelMultipleChoiceField

from guardian.forms import GroupObjectPermissionsForm

from .models import GroupDescription, DEFAULT_ALLOWED_TAGS


# Group Descriptions

class GroupDescriptionCreateForm(ModelForm):
    """A custom ModelForm for creating a GroupDescription"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

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


class GroupDescriptionUpdateForm(ModelForm):
    """A custom ModelForm for updating a GroupDescription"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

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


class GroupPermissionsForm(ModelForm):
    """A custom ModelForm for updating the permissions associated with a group"""

    def __getattribute__(self, name):
        if name == 'label_suffix':
            return ''
        return object.__getattribute__(self, name)

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

    def get_obj_perms_field_widget(self):
        return CheckboxSelectMultiple

    def get_obj_perms_field_choices(self):
        choices = super().get_obj_perms_field_choices()
        return [(codename, name) for (codename, name) in choices
                if not (codename.startswith('delete_') or codename.startswith('add_'))]

    def clean_permissions(self):
        """Remove unused permissions on form submission"""
        permissions = self.cleaned_data['permissions']
        return [permission for permission in permissions
                if not (permission.startswith('delete_') or permission.startswith('add_'))]
