"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

import operator
import os
from pathlib import Path
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError, SuspiciousFileOperation, PermissionDenied
from django.db.models import Q
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, \
                                       PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import default_storage
from django.views.generic.edit import CreateView, UpdateView, DeleteView, \
                                      FormMixin, ProcessFormView
from django_sendfile import sendfile
import humanize
from .models import Resource, Faculty, Department, Agreement, Signature
from .forms import ResourceCreateForm, ResourceUpdateForm, \
                   FacultyCreateForm, FacultyUpdateForm, \
                   DepartmentCreateForm, DepartmentUpdateForm, \
                   AgreementCreateForm, AgreementUpdateForm, \
                   SignatureCreateForm, SignatureSearchForm


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


# Resources

class ResourceList(LoginRequiredMixin, ListView):
    """A view of all Resources"""
    model = Resource
    context_object_name = 'resources'


class ResourceRead(LoginRequiredMixin, DetailView):
    """A view of a Resource"""
    model = Resource
    context_object_name = 'resource'
    template_name_suffix = '_read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agreements = Agreement.objects.filter(resource=self.get_object()).order_by('-created')
        if not self.request.user.has_perm('agreements.view_agreement'):
            agreements = agreements.exclude(hidden=True)
        context['agreements'] = agreements
        return context


class ResourceCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a Resource"""
    model = Resource
    template_name_suffix = '_create_form'
    permission_required = 'agreements.add_resource'
    success_message = '%(name)s was created successfully.'
    form_class = ResourceCreateForm


class ResourceUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a Resource"""
    model = Resource
    context_object_name = 'resource'
    template_name_suffix = '_update_form'
    permission_required = 'agreements.change_resource'
    success_message = '%(name)s was updated successfully.'
    form_class = ResourceUpdateForm


class ResourceDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a Resource"""
    model = Resource
    fields = '__all__'
    context_object_name = 'resource'
    template_name_suffix = '_delete_form'
    permission_required = 'agreements.delete_resource'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('resource_list')


class ResourceAccess(LoginRequiredMixin, DetailView):
    """A view which allows access to files associated with a Resource"""
    model = Resource
    context_object_name = 'resource'
    template_name_suffix = '_access'

    def get(self, request, *args, **kwargs):
        # Has the user signed the newest, unhidden agreement associated with this
        # resource?
        resource = self.get_object()
        try:
            newest_associated_agreement = Agreement.objects.filter(hidden=False, resource=resource) \
                                                           .order_by('-created')[0]
        except IndexError:
            raise Http404("Unable to find associated, unhidden agreement.")
        try:
            newest_associated_agreement.signature_set.filter(signatory=self.request.user).get()
        except Signature.DoesNotExist:
            messages.error(self.request,
                           'You must sign an agreement before accessing files associated with this resource.')
            return redirect(newest_associated_agreement)

        # Access is granted, is the access path a file or a directory?
        resource_scoped_path = os.path.join(resource.slug, self.kwargs['accesspath'])
        try:
            self.path = default_storage.path(resource_scoped_path)  # pylint: disable=attribute-defined-outside-init
            if not os.path.exists(self.path):
                raise Http404("File not found at access path.")
            if os.path.isfile(self.path):
                return sendfile(request, self.path)
        except SuspiciousFileOperation:
            raise PermissionDenied('SuspiciousFileOperation on file access.')

        # Redirect if the file listing doesn't end in a slash
        if self.kwargs['accesspath'] != '' and self.kwargs['accesspath'][-1] != '/':
            return redirect(reverse_lazy('resources_access', args=[resource.slug, self.kwargs['accesspath']+'/']))
        # Render a file listing to the user.
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accesspath'] = self.kwargs['accesspath']
        context['directories'] = []
        context['files'] = []
        for entry in os.scandir(self.path):
            if entry.is_dir():
                directory = {}
                directory['name'] = entry.name
                directory['accesspath'] = os.path.join(self.kwargs['accesspath'], entry.name)
                context['directories'].append(directory)
            else:
                file = {}
                file['name'] = entry.name
                file['accesspath'] = os.path.join(self.kwargs['accesspath'], entry.name)
                file['size'] = humanize.naturalsize(entry.stat().st_size, binary=True)
                context['files'].append(file)
        context['directories'].sort(key=operator.itemgetter('name'))
        context['files'].sort(key=operator.itemgetter('name'))

        if self.kwargs['accesspath'] != '':
            parentdir = str(Path(self.kwargs['accesspath']).parent)
            if parentdir == '.':
                parentdir = ''
            context['parentdir'] = parentdir
        return context


# Faculties

class FacultyList(PermissionRequiredMixin, ListView):
    """A view of all Faculties"""
    model = Faculty
    context_object_name = 'faculties'
    permission_required = 'agreements.view_faculty'


class FacultyRead(PermissionRequiredMixin, DetailView):
    """A view of a Faculty"""
    model = Faculty
    context_object_name = 'faculty'
    template_name_suffix = '_read'
    permission_required = 'agreements.view_faculty'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = context['faculty'].department_set.all()
        return context


class FacultyCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a Faculty"""
    model = Faculty
    template_name_suffix = '_create_form'
    permission_required = 'agreements.add_faculty'
    success_message = '%(name)s was created successfully.'
    form_class = FacultyCreateForm


class FacultyUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a Faculty"""
    model = Faculty
    context_object_name = 'faculty'
    template_name_suffix = '_update_form'
    permission_required = 'agreements.change_faculty'
    success_message = '%(name)s was updated successfully.'
    form_class = FacultyUpdateForm


class FacultyDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a Faculty"""
    model = Faculty
    fields = '__all__'
    context_object_name = 'faculty'
    template_name_suffix = '_delete_form'
    permission_required = 'agreements.delete_faculty'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('faculties_list')


# Departments

class DepartmentList(PermissionRequiredMixin, ListView):
    """A view of all Departments"""
    model = Department
    context_object_name = 'departments'
    permission_required = 'agreements.view_department'


class DepartmentRead(PermissionRequiredMixin, DetailView):
    """A view of a Department"""
    model = Department
    context_object_name = 'department'
    template_name_suffix = '_read'
    permission_required = 'agreements.view_department'


class DepartmentCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a Department"""
    model = Department
    template_name_suffix = '_create_form'
    permission_required = 'agreements.add_department'
    success_message = '%(name)s was created successfully.'
    form_class = DepartmentCreateForm


class DepartmentCreateUnderFaculty(DepartmentCreate):
    """A view to create a Department under a given Faculty"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = get_object_or_404(Faculty, slug=self.kwargs['facultyslug'])
        context['form'].fields['faculty'].initial = faculty.id
        return context


class DepartmentUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a Department"""
    model = Department
    context_object_name = 'department'
    template_name_suffix = '_update_form'
    permission_required = 'agreements.change_department'
    success_message = '%(name)s was updated successfully.'
    form_class = DepartmentUpdateForm


class DepartmentDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a Department"""
    model = Department
    fields = '__all__'
    context_object_name = 'department'
    template_name_suffix = '_delete_form'
    permission_required = 'agreements.delete_department'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('departments_list')


# Agreements

class AgreementList(LoginRequiredMixin, ListView):
    """A view of all Agreements"""
    model = Agreement
    context_object_name = 'agreements'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.has_perm('agreements.view_agreement'):
            qs = qs.exclude(hidden=True)
        return qs


class AgreementRead(FormMixin, DetailView, ProcessFormView):
    """A view of an Agreement"""
    model = Agreement
    context_object_name = 'agreement'
    template_name_suffix = '_read'
    form_class = SignatureCreateForm

    def get_success_url(self):
        return reverse_lazy('agreements_read', kwargs={'slug': self.kwargs['slug']})

    def form_valid(self, form):
        signature = form.save(commit=False)
        signature.agreement = self.get_object()
        signature.signatory = self.request.user
        signature.username = self.request.user.username
        signature.first_name = self.request.user.first_name
        signature.last_name = self.request.user.last_name
        signature.email = self.request.user.email
        try:
            signature.full_clean()
        except ValidationError:
            messages.error(self.request, 'Agreement already signed.')
            return redirect(self.get_object())
        signature.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['associated_signature'] = (
                context['agreement'].signature_set.filter(signatory=self.request.user).get()
                )
        except Signature.DoesNotExist:
            context['associated_signature'] = None
        return context


class AgreementCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create an Agreement"""
    model = Agreement
    template_name_suffix = '_create_form'
    permission_required = 'agreements.add_agreement'
    success_message = '%(title)s was created successfully.'
    form_class = AgreementCreateForm


class AgreementUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update an Agreement"""
    model = Agreement
    context_object_name = 'agreement'
    template_name_suffix = '_update_form'
    permission_required = 'agreements.change_agreement'
    success_message = '%(title)s was updated successfully.'
    form_class = AgreementUpdateForm


class AgreementDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete an Agreement"""
    model = Agreement
    fields = '__all__'
    context_object_name = 'agreement'
    template_name_suffix = '_delete_form'
    permission_required = 'agreements.delete_agreement'
    success_message = '%(title)s was deleted successfully.'
    success_url = reverse_lazy('agreements_list')


# Signatures

class SignatureList(PermissionRequiredMixin, FormMixin, ListView):
    """A view to list and search through Signatures of an Agreement"""
    model = Signature
    context_object_name = 'signatures'
    permission_required = 'agreements.view_signature'
    form_class = SignatureSearchForm
    paginate_by = 15

    def get_queryset(self):
        qs = Signature.objects.all()
        if 'agreementslug' in self.kwargs:
            self.agreement = get_object_or_404(  # pylint: disable=attribute-defined-outside-init
                Agreement, slug=self.kwargs['agreementslug']
            )
            qs = qs.filter(agreement=self.agreement)
        if 'search' in self.request.GET:
            q_param = self.request.GET['search']
            if q_param != '':
                qs = qs.filter(
                    Q(username__icontains=q_param) |
                    Q(first_name__icontains=q_param) |
                    Q(last_name__icontains=q_param) |
                    Q(email__icontains=q_param) |
                    Q(department__name__icontains=q_param) |
                    Q(department__faculty__name__icontains=q_param)
                )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['agreement'] = self.agreement
        except AttributeError:
            context['agreement'] = None
        context['form'].fields['search'].initial = self.request.GET.get('search', default='')
        return context
