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
from .forms import UserSearchForm, UserUpdateForm, UserUberUpdateForm, \
                   GroupDescriptionCreateForm, GroupDescriptionUpdateForm, GroupPermissionsForm


# Custom Mixins

class SuccessMessageIfChangedMixin:
    """Add a success message on successful form submission if the form has changed."""
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


class IsStaffMixin(UserPassesTestMixin):
    """A custom access mixin which ensures the user is a staff member"""
    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff


# Staff

class UserList(IsStaffMixin, FormMixin, ListView):
    """A view of all users"""
    context_object_name = 'users'
    form_class = UserSearchForm
    model = User
    ordering = ['-is_staff', '-date_joined']
    paginate_by = 15
    template_name = 'accounts/user_list.html'

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


class UserRead(IsStaffMixin, DetailView):
    """A view of a user"""
    context_object_name = 'user_detail'
    model = User
    slug_field = 'username'
    template_name = 'accounts/user_read.html'


class UserUpdate(IsStaffMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a user"""
    context_object_name = 'user_detail'
    form_class = UserUpdateForm
    model = User
    slug_field = 'username'
    template_name_suffix = '_update_form'

    def get_success_message(self, cleaned_data):
        return f'{self.get_object().username} has been updated successfully.'

    def get_success_url(self):
        return reverse_lazy('users_read', kwargs={'slug': self.get_object().username})

    def get_form_class(self):
        if self.request.user.is_superuser:
            return UserUberUpdateForm
        return self.form_class

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fullname'] = f'{self.get_object().first_name} {self.get_object().last_name}'
        return context


# GroupDescriptions

class GroupDescriptionList(PermissionRequiredMixin, ListView):
    """A view of all group descriptions"""
    context_object_name = 'groupdescriptions'
    model = GroupDescription
    ordering = 'name'
    paginate_by = 15
    permission_required = 'accounts.view_groupdescription'


class GroupDescriptionRead(PermissionRequiredMixin, DetailView):
    """A view of a group description"""
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
    """A view to update a group description"""
    context_object_name = 'groupdescription'
    form_class = GroupDescriptionUpdateForm
    model = GroupDescription
    permission_required = 'accounts.change_groupdescription'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class GroupDescriptionUpdatePermissions(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a group description"""
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
    """A view to delete a group description"""
    context_object_name = 'groupdescription'
    fields = '__all__'
    model = GroupDescription
    permission_required = 'accounts.delete_groupdescription'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('group_descriptions_list')
    template_name_suffix = '_delete_form'


# Login and Logout

class Login(LoginView):
    """The user authentication login view"""
    template_name = 'accounts/login.html'


class Logout(LogoutView):
    """The user authentication login view"""
    template_name = 'accounts/logout.html'
