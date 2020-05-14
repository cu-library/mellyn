"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin, UpdateView, CreateView, DeleteView

from .models import User, GroupDescription
from .forms import GroupDescriptionCreateForm, GroupDescriptionUpdateForm, \
                   GroupPermissionsForm, \
                   UserSearchForm, UserUpdateForm, UserUberUpdateForm


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

class UserList(UserPassesTestMixin, FormMixin, ListView):
    """A view of all staff users"""
    context_object_name = 'users'
    form_class = UserSearchForm
    model = User
    ordering = ['-is_staff', '-date_joined']
    paginate_by = 15
    template_name = 'accounts/user_list.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        qs = super().get_queryset().exclude(username='AnonymousUser')
        q_param = self.request.GET.get('search', '')
        if q_param != '':
            qs = qs.search(q_param)
        return qs

    def get_initial(self):
        initial = super().get_initial()
        initial['search'] = self.request.GET.get('search', default='')
        return initial


class UserRead(UserPassesTestMixin, DetailView):
    """A view of a staff user"""
    context_object_name = 'user_detail'
    model = User
    slug_field = 'username'
    template_name = 'accounts/user_read.html'

    def test_func(self):
        return self.request.user.is_staff


class UserUpdate(UserPassesTestMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a GroupDescription"""
    context_object_name = 'user_detail'
    model = User
    form_class = UserUpdateForm
    slug_field = 'username'
    success_message = 'User was updated successfully.'
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse_lazy('user_read', kwargs={'slug': self.kwargs['slug']})

    def test_func(self):
        return self.request.user.is_staff

    def get_form_class(self):
        if self.request.user.is_superuser:
            return UserUberUpdateForm
        return self.form_class


# GroupDescriptions

class GroupDescriptionList(PermissionRequiredMixin, ListView):
    """A view of all GroupDescription"""
    context_object_name = 'groupdescriptions'
    model = GroupDescription
    permission_required = 'accounts.view_groupdescription'


class GroupDescriptionRead(PermissionRequiredMixin, DetailView):
    """A view of a GroupDescription"""
    context_object_name = 'groupdescription'
    model = GroupDescription
    permission_required = 'accounts.view_groupdescription'
    template_name_suffix = '_read'


class GroupDescriptionCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a GroupDescription"""
    form_class = GroupDescriptionCreateForm
    model = GroupDescription
    permission_required = 'accounts.add_groupdescription'
    success_message = '%(name)s was created successfully.'
    template_name_suffix = '_create_form'


class GroupDescriptionUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a GroupDescription"""
    context_object_name = 'groupdescription'
    form_class = GroupDescriptionUpdateForm
    model = GroupDescription
    permission_required = 'accounts.change_groupdescription'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class GroupDescriptionUpdatePermissions(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a GroupDescription"""
    context_object_name = 'group'
    form_class = GroupPermissionsForm
    model = Group
    permission_required = 'accounts.change_groupdescription'
    queryset = GroupDescription.objects.all()
    success_message = 'Permissions for %(name)s updated successfully.'
    template_name = 'accounts/groupdescription_update_permissions_form.html'

    def get_object(self, queryset=None):
        group_description = super().get_object(queryset)
        return group_description.group

    def get_success_url(self):
        return reverse_lazy('groupdescriptions_read', args=[super().get_object(None).slug])

    def get_success_message(self, cleaned_data):
        return self.success_message % {'name': super().get_object(None).name}


class GroupDescriptionDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a GroupDescription"""
    context_object_name = 'groupdescription'
    fields = '__all__'
    model = GroupDescription
    permission_required = 'accounts.delete_groupdescription'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('group_descriptions_list')
    template_name_suffix = '_delete_form'


# Login and Logout

class Login(LoginView):
    """A the user authentication login view"""
    template_name = 'accounts/login.html'


class Logout(LogoutView):
    """A the user authentication login view"""
    template_name = 'accounts/logout.html'
