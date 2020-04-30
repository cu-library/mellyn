"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.contrib import messages
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from .models import User, GroupDescription
from .forms import GroupDescriptionCreateForm, GroupDescriptionUpdateForm, GroupPermissionsForm


# Custom Mixins

class SuccessMessageIfChangedMixin:
    """
    Add a success message on successful form submission if the form has changed.
    """
    success_message = ''

    def form_valid(self, form):  # pylint: disable=missing-function-docstring
        response = super().form_valid(form)
        if form.has_changed():
            success_message = self.get_success_message(form.cleaned_data)
            if success_message:
                messages.success(self.request, success_message)
        return response

    def get_success_message(self, cleaned_data):  # pylint: disable=missing-function-docstring
        return self.success_message % cleaned_data


# Staff

class StaffUserList(UserPassesTestMixin, ListView):
    """A view of all staff users"""
    model = User
    context_object_name = 'staff'
    queryset = User.objects.filter(is_staff=True)
    template_name = 'accounts/staff_list.html'

    def test_func(self):
        return self.request.user.is_staff


class StaffUserRead(UserPassesTestMixin, DetailView):
    """A view of a staff user"""
    model = User
    slug_field = 'username'
    context_object_name = 'staff_user'
    template_name = 'accounts/staff_read.html'
    queryset = User.objects.filter(is_staff=True)

    def test_func(self):
        return self.request.user.is_staff


# GroupDescriptions

class GroupDescriptionList(PermissionRequiredMixin, ListView):
    """A view of all GroupDescription"""
    model = GroupDescription
    context_object_name = 'groupdescriptions'
    permission_required = 'accounts.view_groupdescription'


class GroupDescriptionRead(PermissionRequiredMixin, DetailView):
    """A view of a GroupDescription"""
    model = GroupDescription
    context_object_name = 'groupdescription'
    template_name_suffix = '_read'
    permission_required = 'accounts.view_groupdescription'


class GroupDescriptionCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a GroupDescription"""
    model = GroupDescription
    template_name_suffix = '_create_form'
    permission_required = 'accounts.add_groupdescription'
    success_message = '%(name)s was created successfully.'
    form_class = GroupDescriptionCreateForm


class GroupDescriptionUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a GroupDescription"""
    model = GroupDescription
    template_name_suffix = '_update_form'
    context_object_name = 'groupdescription'
    permission_required = 'accounts.change_groupdescription'
    success_message = '%(name)s was updated successfully.'
    form_class = GroupDescriptionUpdateForm


class GroupDescriptionUpdatePermissions(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a GroupDescription"""
    model = Group
    template_name = 'accounts/groupdescription_update_permissions_form.html'
    context_object_name = 'group'
    permission_required = 'accounts.change_groupdescription'
    success_message = 'Permissions for %(name)s updated successfully.'
    queryset = GroupDescription.objects.all()
    form_class = GroupPermissionsForm

    def get_object(self, queryset=None):
        group_description = super().get_object(queryset)
        return group_description.group

    def get_success_url(self):
        return reverse_lazy('groupdescriptions_read', args=[super().get_object(None).slug])

    def get_success_message(self, cleaned_data):
        return self.success_message % {'name': super().get_object(None).name}


class GroupDescriptionDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a GroupDescription"""
    model = GroupDescription
    fields = '__all__'
    context_object_name = 'groupdescription'
    template_name_suffix = '_delete_form'
    permission_required = 'accounts.delete_groupdescription'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('group_descriptions_list')


# Login and Logout

class Login(LoginView):
    """A the user authentication login view"""
    template_name = 'accounts/login.html'


class Logout(LogoutView):
    """A the user authentication login view"""
    template_name = 'accounts/logout.html'
