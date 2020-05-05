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
from accounts.models import GroupDescription
from .models import Resource, LicenseCode, Faculty, Department, Agreement, Signature
from .forms import ResourceCreateForm, ResourceUpdateForm, \
                   LicenseCodeAddForm, \
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
    context_object_name = 'resources'
    model = Resource
    ordering = 'name'
    paginate_by = 15


class ResourceRead(LoginRequiredMixin, DetailView):
    """A view of a Resource"""
    context_object_name = 'resource'
    model = Resource
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
    form_class = ResourceCreateForm
    model = Resource
    permission_required = 'agreements.add_resource'
    success_message = '%(name)s was created successfully.'
    template_name_suffix = '_create_form'


class ResourceUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a Resource"""
    context_object_name = 'resource'
    form_class = ResourceUpdateForm
    model = Resource
    permission_required = 'agreements.change_resource'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class ResourceDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a Resource"""
    context_object_name = 'resource'
    fields = '__all__'
    model = Resource
    permission_required = 'agreements.delete_resource'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('resource_list')
    template_name_suffix = '_delete_form'


class ResourcePermissions(PermissionRequiredMixin, SuccessMessageMixin, DetailView):
    """A view which provides view and edit functionality for permissions on this resource"""
    context_object_name = 'resource'
    model = Resource
    permission_required = 'agreements.add_resource'
    template_name = 'agreements/resource_permissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['global_permissions'] = []
        related_group_permissions = (
            GroupDescription.objects
            .filter(group__permissions__content_type__model='resource')
            .distinct()
            .order_by('name')
        )
        for groupdescription in related_group_permissions:
            permissions = (
                groupdescription
                .group
                .permissions
                .filter(content_type__model='resource')
                .distinct()
            )
            context['global_permissions'].append((groupdescription, permissions))
        return context


class ResourceAccess(LoginRequiredMixin, DetailView):
    """A view which allows access to files associated with a Resource"""
    context_object_name = 'resource'
    model = Resource
    template_name_suffix = '_access'

    def get(self, request, *args, **kwargs):
        # Has the user signed the newest, unhidden agreement associated with this
        # resource?
        resource = self.get_object()
        try:
            newest_associated_agreement = Agreement.objects.filter(hidden=False, resource=resource) \
                                                           .order_by('-created')[0]
        except IndexError:
            raise Http404('Unable to find associated, unhidden agreement.')
        try:
            newest_associated_agreement.signature_set.filter(signatory=self.request.user).get()
        except Signature.DoesNotExist:
            messages.error(self.request,
                           f'You must sign this agreement before accessing files associated with {resource.name}.')
            return redirect(newest_associated_agreement)

        # Access is granted, is the access path a file or a directory?
        resource_scoped_path = os.path.join(resource.slug, self.kwargs['accesspath'])
        try:
            self.path = default_storage.path(resource_scoped_path)  # pylint: disable=attribute-defined-outside-init
            if not os.path.exists(self.path):
                raise Http404('File not found at access path.')
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


# License Codes

class ResourceLicenseCode(PermissionRequiredMixin, ListView):
    """A view of a Resource"""
    context_object_name = 'license_codes'
    model = LicenseCode
    ordering = 'name'
    paginate_by = 15
    permission_required = 'agreements.view_licensecode'
    template_name_suffix = '_list_for_resource'

    def get_queryset(self):
        qs = super().get_queryset()
        self.resource = get_object_or_404(Resource, slug=self.kwargs['slug'])  # NOQA # pylint: disable=attribute-defined-outside-init
        return qs.filter(resource=self.resource).order_by('signature', 'added')

    def get_context_data(self, **kwargs):  # pylint: disable=arguments-differ
        context = super().get_context_data(**kwargs)
        context['resource'] = self.resource
        return context


class ResourceLicenseCodeAdd(FormMixin, DetailView, ProcessFormView):
    """A view where a staff user can add more License Codes to a Resource"""
    context_object_name = 'resource'
    form_class = LicenseCodeAddForm
    model = Resource
    template_name = 'agreements/licensecode_add_form.html'

    def get_success_url(self):
        return reverse_lazy('resources_codes', kwargs={'slug': self.kwargs['slug']})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'resource': self.get_object()})
        return kwargs

    def get_context_data(self, **kwargs):
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        codes = form.cleaned_data['codes']
        for code in codes:
            license_code = LicenseCode(resource=self.get_object(), code=code)
            try:
                license_code.full_clean()
            except ValidationError:
                messages.error(self.request, f'Error when saving license code {code}, possible duplicate.')
                return redirect(reverse_lazy('resources_codes', kwargs={'slug': self.kwargs['slug']}))
            license_code.save()
        messages.success(self.request, f'{len(codes)} new access codes added to {self.get_object().name}.')
        return super().form_valid(form)


# Faculties

class FacultyList(PermissionRequiredMixin, ListView):
    """A view of all Faculties"""
    context_object_name = 'faculties'
    model = Faculty
    permission_required = 'agreements.view_faculty'


class FacultyRead(PermissionRequiredMixin, DetailView):
    """A view of a Faculty"""
    context_object_name = 'faculty'
    model = Faculty
    permission_required = 'agreements.view_faculty'
    template_name_suffix = '_read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = context['faculty'].department_set.all()
        return context


class FacultyCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a Faculty"""
    form_class = FacultyCreateForm
    model = Faculty
    permission_required = 'agreements.add_faculty'
    success_message = '%(name)s was created successfully.'
    template_name_suffix = '_create_form'


class FacultyUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a Faculty"""
    context_object_name = 'faculty'
    form_class = FacultyUpdateForm
    model = Faculty
    permission_required = 'agreements.change_faculty'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class FacultyDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a Faculty"""
    context_object_name = 'faculty'
    fields = '__all__'
    model = Faculty
    permission_required = 'agreements.delete_faculty'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('faculties_list')
    template_name_suffix = '_delete_form'


# Departments

class DepartmentList(PermissionRequiredMixin, ListView):
    """A view of all Departments"""
    context_object_name = 'departments'
    model = Department
    permission_required = 'agreements.view_department'


class DepartmentRead(PermissionRequiredMixin, DetailView):
    """A view of a Department"""
    context_object_name = 'department'
    model = Department
    permission_required = 'agreements.view_department'
    template_name_suffix = '_read'


class DepartmentCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a Department"""
    form_class = DepartmentCreateForm
    model = Department
    permission_required = 'agreements.add_department'
    success_message = '%(name)s was created successfully.'
    template_name_suffix = '_create_form'


class DepartmentCreateUnderFaculty(DepartmentCreate):
    """A view to create a Department under a given Faculty"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = get_object_or_404(Faculty, slug=self.kwargs['facultyslug'])
        context['form'].fields['faculty'].initial = faculty.id
        return context


class DepartmentUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a Department"""
    context_object_name = 'department'
    form_class = DepartmentUpdateForm
    model = Department
    permission_required = 'agreements.change_department'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class DepartmentDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a Department"""
    context_object_name = 'department'
    fields = '__all__'
    model = Department
    permission_required = 'agreements.delete_department'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('departments_list')
    template_name_suffix = '_delete_form'


# Agreements

class AgreementList(LoginRequiredMixin, ListView):
    """A view of all Agreements"""
    context_object_name = 'agreements'
    model = Agreement
    ordering = 'title'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.has_perm('agreements.view_agreement'):
            qs = qs.exclude(hidden=True)
        return qs


class AgreementRead(LoginRequiredMixin, FormMixin, DetailView, ProcessFormView):
    """A view of an Agreement"""
    context_object_name = 'agreement'
    form_class = SignatureCreateForm
    model = Agreement
    template_name_suffix = '_read'

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
        license_code = (
            LicenseCode.objects.select_for_update(skip_locked=True)
            .filter(signature=None, resource=self.get_object().resource)
            .order_by('added').first()
            )
        if license_code:
            license_code.signature = signature
            license_code.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
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
    form_class = AgreementCreateForm
    model = Agreement
    permission_required = 'agreements.add_agreement'
    success_message = '%(title)s was created successfully.'
    template_name_suffix = '_create_form'


class AgreementUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update an Agreement"""
    context_object_name = 'agreement'
    form_class = AgreementUpdateForm
    model = Agreement
    permission_required = 'agreements.change_agreement'
    success_message = '%(title)s was updated successfully.'
    template_name_suffix = '_update_form'


class AgreementDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete an Agreement"""
    context_object_name = 'agreement'
    fields = '__all__'
    model = Agreement
    permission_required = 'agreements.delete_agreement'
    success_message = '%(title)s was deleted successfully.'
    success_url = reverse_lazy('agreements_list')
    template_name_suffix = '_delete_form'


# Signatures

class SignatureList(PermissionRequiredMixin, FormMixin, ListView):
    """A view to list and search through Signatures of an Agreement"""
    context_object_name = 'signatures'
    form_class = SignatureSearchForm
    model = Signature
    ordering = '-signed_at'
    paginate_by = 15
    permission_required = 'agreements.view_signature'

    def get_queryset(self):
        qs = super().get_queryset()
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
