"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from pathlib import Path
import operator
import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError, SuspiciousFileOperation, PermissionDenied
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin, ProcessFormView

from csv_export.views import CSVExportView
from django_sendfile import sendfile
import humanize

from accounts.models import GroupDescription
from .forms import ResourceCreateForm, ResourceUpdateForm, \
                   LicenseCodeForm, \
                   FacultyCreateForm, FacultyUpdateForm, \
                   DepartmentCreateForm, DepartmentUpdateForm, \
                   AgreementCreateForm, AgreementUpdateForm, \
                   SignatureCreateForm, SignatureSearchForm
from .models import Resource, LicenseCode, Faculty, Department, Agreement, Signature, FileDownloadEvent


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
        agreements = Agreement.objects.all()
        if not self.request.user.has_perm('agreements.view_agreement'):
            agreements = agreements.exclude(hidden=True)
        context['agreements'] = agreements.for_resource_with_signature(self.get_object(), self.request.user)
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
    """A view which provides view and edit functionality for permissions on this Resource"""
    context_object_name = 'resource'
    model = Resource
    permission_required = 'agreements.add_resource'
    template_name = 'agreements/resource_permissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['global_permissions'] = (GroupDescription.objects
                                         .for_model_with_permissions('resource'))
        return context


class ResourceAccess(LoginRequiredMixin, DetailView):
    """A view which allows access to files associated with a Resource"""
    context_object_name = 'resource'
    model = Resource
    template_name_suffix = '_access'

    def get(self, request, *args, **kwargs):
        resource = self.get_object()
        # Does a valid associated agreement exist for this resource?
        associated_agreement = (Agreement.objects
                                .filter(resource=resource)
                                .valid()
                                .order_by('-created')
                                .first())
        if associated_agreement is None:
            raise Http404('Unable to find valid and unhidden agreement.')

        # Has the user signed that agreement?
        try:
            associated_agreement.signature_set.filter(signatory=self.request.user).get()
        except Signature.DoesNotExist:
            messages.error(self.request,
                           f'You must sign this agreement before accessing files associated with {resource.name}.')
            # Attach some data to the session so that we can redirect back to this request later
            request.session['access_attempt'] = (resource.slug, self.kwargs['accesspath'])
            return redirect(associated_agreement)

        # Access is granted, is the access path a file or a directory?
        resource_scoped_path = os.path.join(resource.slug, self.kwargs['accesspath'])
        try:
            self.path = default_storage.path(resource_scoped_path)  # pylint: disable=attribute-defined-outside-init
            if not os.path.exists(self.path):
                raise Http404('File or directory not found at access path.')
            if os.path.isfile(self.path):
                FileDownloadEvent.objects.get_or_create_if_no_duplicates_past_5_minutes(resource,
                                                                                        self.kwargs['accesspath'],
                                                                                        request.session.session_key)
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


class ResourceAccessFileStats(PermissionRequiredMixin, DetailView):
    """A view which provides download stats for a Resources's files"""
    context_object_name = 'resource'
    model = Resource
    permission_required = 'agreements.view_resource'
    template_name = 'agreements/resource_file_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file_stats'] = FileDownloadEvent.objects.download_count_per_path_for_resource(self.get_object())
        return context


# License Codes

class ResourceLicenseCode(PermissionRequiredMixin, ListView):
    """A view of LicenseCodes associated with a Resource"""
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
    """A view to add more License Codes to a Resource"""
    context_object_name = 'resource'
    form_class = LicenseCodeForm
    model = Resource
    template_name = 'agreements/licensecode_add_form.html'

    def get_success_url(self):
        return reverse_lazy('resources_codes', kwargs={'slug': self.kwargs['slug']})

    def get_context_data(self, **kwargs):
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        codes = form.cleaned_data['codes']
        successes = 0
        for code in codes:
            if not LicenseCode.objects.filter(resource=self.get_object(), code=code).exists():
                license_code = LicenseCode(resource=self.get_object(), code=code)
                try:
                    license_code.full_clean()
                except ValidationError:
                    messages.error(self.request, f'Error when saving license code {code}, possible duplicate.')
                    return redirect(reverse_lazy('resources_codes', kwargs={'slug': self.kwargs['slug']}))
                license_code.save()
                successes += 1
        if successes > 1:
            messages.success(self.request,
                             f'{humanize.apnumber(successes).capitalize()} new license codes '
                             f'added to {self.get_object().name}.')
        elif successes == 1:
            messages.success(self.request, f'One new license code added to {self.get_object().name}.')
        return super().form_valid(form)


class ResourceLicenseCodeUpdate(ResourceLicenseCodeAdd):
    """A view to update the License Codes of a Resource"""
    context_object_name = 'resource'
    form_class = LicenseCodeForm
    model = Resource
    template_name = 'agreements/licensecode_update_form.html'

    def get_initial(self):
        codes = ""
        for license_code in LicenseCode.objects.filter(resource=self.get_object(), signature__isnull=True):
            codes += f'{license_code.code}\n'
        return {'codes': codes}

    def form_valid(self, form):
        codes = form.cleaned_data['codes']
        codes_to_delete = LicenseCode.objects.filter(resource=self.get_object(), signature__isnull=True)
        for code in codes:
            codes_to_delete = codes_to_delete.exclude(code=code)
        deleted, _ = codes_to_delete.delete()
        if deleted > 1:
            messages.warning(self.request,
                             f'{humanize.apnumber(deleted).capitalize()} license codes '
                             f'removed from {self.get_object().name}.')
        elif deleted == 1:
            messages.warning(self.request, f'One license code deleted from {self.get_object().name}.')
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'faculty': get_object_or_404(Faculty, slug=self.kwargs['facultyslug'])}
        return kwargs


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


class AgreementRead(LoginRequiredMixin, UserPassesTestMixin, FormMixin, DetailView, ProcessFormView):
    """A view of an Agreement"""
    context_object_name = 'agreement'
    form_class = SignatureCreateForm
    model = Agreement
    template_name_suffix = '_read'

    def test_func(self):
        # If the agreement isn't valid to see, you have to have the right permissions.
        if self.get_object().valid():
            return True
        return self.request.user.has_perm('agreements.view_agreement')

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
        with transaction.atomic():
            license_code = (LicenseCode.objects
                            .select_for_update(skip_locked=True)
                            .filter(signature=None, resource=self.get_object().resource)
                            .order_by('added').first())
            if license_code:
                license_code.signature = signature
                license_code.save()
        if 'access_attempt' in self.request.session:
            slug, accesspath = self.request.session.pop('access_attempt', (self.get_object().resource.slug, ''))
            return redirect(reverse_lazy('resources_access', kwargs={'slug': slug, 'accesspath': accesspath}))
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
        q_param = self.request.GET.get('search', '')
        if q_param != '':
            qs = qs.search(q_param)
        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'search': self.request.GET.get('search', default='')}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agreement'] = getattr(self, 'agreement', None)
        context['count_per_department'] = self.get_queryset().count_per_department()
        context['count_per_faculty'] = self.get_queryset().count_per_faculty()
        return context


class SignatureCSV(PermissionRequiredMixin, CSVExportView):
    """A view to download the Signatures associated with an agreement as a CSV file"""
    fields = ('agreement__title', 'username', 'first_name',
              'last_name', 'email', 'department__name',
              'department__faculty__name', 'signed_at')
    model = Signature
    permission_required = 'agreements.view_signature'

    def get_header_name(self, model, field_name):
        if field_name == 'agreement__title':
            return 'Agreement'
        if field_name == 'department__name':
            return 'Department'
        if field_name == 'department__faculty__name':
            return 'Faculty'
        return super().get_header_name(model, field_name)

    def get_filename(self, queryset):
        return f"{now().strftime('%Y-%m-%d')}-{self.agreement.slug}-signatures.csv"

    def get_queryset(self):
        qs = super().get_queryset()
        self.agreement = get_object_or_404(  # pylint: disable=attribute-defined-outside-init
            Agreement, slug=self.kwargs['agreementslug']
        )
        qs = qs.filter(agreement=self.agreement)
        return qs
