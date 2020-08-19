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
from django.views.generic.list import MultipleObjectMixin

from csv_export.views import CSVExportView
from django_sendfile import sendfile
from guardian.mixins import PermissionRequiredMixin as GuardianPermissionRequiredMixin
import humanize

from accounts.models import GroupDescription
from accounts.forms import CustomGroupObjectPermissionsForm
from .forms import ResourceCreateForm, ResourceUpdateForm, \
                   LicenseCodeForm, \
                   FacultyCreateForm, FacultyUpdateForm, \
                   DepartmentCreateForm, DepartmentUpdateForm, \
                   AgreementCreateForm, AgreementUpdateForm, \
                   SignatureCreateForm, SignatureSearchForm
from .models import Resource, LicenseCode, Faculty, Department, Agreement, Signature, FileDownloadEvent


# Library functions that should exist

def has_perm(user, perm, obj):
    """
    Return true is has_perm on the user would return true for either the
    object or global permission check.
    """
    return user.has_perm(perm) or user.has_perm(perm, obj)


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


class PermissionRequiredCheckGlobalMixin(GuardianPermissionRequiredMixin):
    """A subclass of Guardian's PermissionRequiredMixin that checks the global permissions first"""
    accept_global_perms = True
    raise_exception = True


# Resources

class ResourceList(LoginRequiredMixin, ListView):
    """A view of all resources"""
    context_object_name = 'resources'
    model = Resource
    ordering = 'name'
    paginate_by = 15
    template_name = 'agreements/resource_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        return [resource for resource in queryset
                if (not resource.hidden) or
                has_perm(self.request.user, 'agreements.view_resource', resource)]


class ResourceRead(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """A view of a resource"""
    context_object_name = 'resource'
    model = Resource
    template_name_suffix = '_read'

    def test_func(self):
        resource = self.get_object()
        # If the resource is hidden, you have to have the right permissions.
        if not resource.hidden:
            return True
        return has_perm(self.request.user, 'agreements.view_resource', resource)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agreements = Agreement.objects.for_resource_with_signature(self.get_object(), self.request.user)
        context['can_edit'] = has_perm(self.request.user, 'agreements.change_resource', context['resource'])
        context['can_view_file_access_stats'] = has_perm(self.request.user,
                                                         'agreements.resource_view_file_access_stats',
                                                         context['resource'])
        context['can_view_licensecodes'] = has_perm(self.request.user,
                                                    'agreements.resource_view_licensecodes',
                                                    context['resource'])
        context['agreements'] = [a for a in agreements
                                 if (not a.hidden) or
                                 has_perm(self.request.user, 'agreements.view_agreement', a)]
        return context


class ResourceCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a resource"""
    form_class = ResourceCreateForm
    model = Resource
    permission_required = 'agreements.add_resource'
    success_message = '%(name)s was created successfully.'
    template_name_suffix = '_create_form'


class ResourceUpdate(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin,
                     SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a resource"""
    context_object_name = 'resource'
    form_class = ResourceUpdateForm
    model = Resource
    permission_required = 'agreements.change_resource'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class ResourceDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a resource"""
    context_object_name = 'resource'
    fields = '__all__'
    model = Resource
    permission_required = 'agreements.delete_resource'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('resources_list')
    template_name_suffix = '_delete_form'


class ResourcePermissions(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin, DetailView):
    """A view which reports on the permissions on this resource"""
    context_object_name = 'resource'
    model = Resource
    permission_required = 'agreements.change_resource'
    template_name = 'agreements/resource_permissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['global_permissions'] = GroupDescription.objects.for_model_with_permissions('resource')
        context['object_permissions'] = (GroupDescription.objects
                                         .for_object_with_groupobjectpermissions('resource', context['resource'].id))
        return context


class ResourcePermissionsGroups(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin, DetailView):
    """A view which lists groups"""
    context_object_name = 'resource'
    model = Resource
    permission_required = 'agreements.change_resource'
    template_name = 'agreements/resource_permissions_groups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_permissions'] = (GroupDescription.objects
                                         .for_object_with_groupobjectpermissions('resource', context['resource'].id))
        context['groupdescriptions'] = []
        groupdescriptions = GroupDescription.objects.all().order_by('name')
        # .difference() would be better here but it causes an error.
        for groupdescription in groupdescriptions:
            if groupdescription not in context['object_permissions']:
                context['groupdescriptions'].append(groupdescription)
        return context


class ResourcePermissionsGroupUpdate(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin,
                                     SuccessMessageIfChangedMixin, FormMixin, DetailView, ProcessFormView):
    """A view which updates the per-object permissions of a resource for a group"""
    context_object_name = 'resource'
    form_class = CustomGroupObjectPermissionsForm
    model = Resource
    permission_required = 'agreements.change_resource'
    template_name = 'agreements/resource_permissions_group_update.html'

    def get_success_url(self):
        return reverse_lazy('resources_permissions_groups', kwargs={'slug': self.kwargs['slug']})

    def get_success_message(self, cleaned_data):
        return f'Object permissions on {self.get_object().name} have been updated successfully.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'group': get_object_or_404(GroupDescription, slug=self.kwargs['groupdescriptionslug']).group,
            'obj': self.get_object(),
        })
        return kwargs

    def get_context_data(self, **kwargs):
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = super().get_context_data(**kwargs)
        context['groupdescription'] = get_object_or_404(GroupDescription, slug=self.kwargs['groupdescriptionslug'])
        return context

    def form_valid(self, form):
        form.save_obj_perms()
        return super().form_valid(form)


class ResourceAccess(LoginRequiredMixin, DetailView):
    """A view which allows access to files associated with a resource"""
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
            if '..' in resource_scoped_path:
                raise SuspiciousFileOperation()
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


class ResourceAccessFileStats(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin, DetailView):
    """A view which provides download stats for a resources's files"""
    context_object_name = 'resource'
    model = Resource
    permission_required = 'agreements.resource_view_file_access_stats'
    template_name = 'agreements/resource_file_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file_stats'] = FileDownloadEvent.objects.download_count_per_path_for_resource(context['resource'])
        return context


# License Codes

class ResourceLicenseCode(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin, DetailView, MultipleObjectMixin):
    """A view of license codes associated with a resource"""
    context_object_name = 'resource'
    model = Resource
    paginate_by = 15
    permission_required = 'agreements.resource_view_licensecodes'
    template_name = 'agreements/resource_licensecode_list.html'

    def get_context_data(self, **kwargs):  # pylint: disable=arguments-differ
        resource = self.get_object()
        license_codes = LicenseCode.objects.filter(resource=resource).order_by('signature', 'added')
        context = super().get_context_data(object_list=license_codes, **kwargs)
        context['license_codes'] = context['object_list']
        context['can_change_licensecodes'] = has_perm(self.request.user,
                                                      'agreements.resource_change_licensecodes',
                                                      context['resource'])
        return context


class ResourceLicenseCodeAdd(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin,
                             FormMixin, DetailView, ProcessFormView):
    """A view to add more license codes to a resource"""
    context_object_name = 'resource'
    form_class = LicenseCodeForm
    model = Resource
    permission_required = 'agreements.resource_change_licensecodes'
    template_name = 'agreements/resource_licensecode_add_form.html'

    def get_success_url(self):
        return reverse_lazy('resources_codes_list', kwargs={'slug': self.kwargs['slug']})

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
                    return redirect(reverse_lazy('resources_codes_list', kwargs={'slug': self.kwargs['slug']}))
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
    """A view to update the license codes of a resource"""
    context_object_name = 'resource'
    form_class = LicenseCodeForm
    model = Resource
    permission_required = 'agreements.resource_change_licensecodes'
    template_name = 'agreements/resource_licensecode_update_form.html'

    def get_initial(self):
        codes = ''
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
    """A view of all faculties"""
    context_object_name = 'faculties'
    model = Faculty
    permission_required = 'agreements.view_faculty'


class FacultyRead(PermissionRequiredMixin, DetailView):
    """A view of a faculty"""
    context_object_name = 'faculty'
    model = Faculty
    permission_required = 'agreements.view_faculty'
    template_name_suffix = '_read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = context['faculty'].department_set.all()
        return context


class FacultyCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a faculty"""
    form_class = FacultyCreateForm
    model = Faculty
    permission_required = 'agreements.add_faculty'
    success_message = '%(name)s was created successfully.'
    template_name_suffix = '_create_form'


class FacultyUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a faculty"""
    context_object_name = 'faculty'
    form_class = FacultyUpdateForm
    model = Faculty
    permission_required = 'agreements.change_faculty'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class FacultyDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a faculty"""
    context_object_name = 'faculty'
    fields = '__all__'
    model = Faculty
    permission_required = 'agreements.delete_faculty'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('faculties_list')
    template_name_suffix = '_delete_form'


# Departments

class DepartmentList(PermissionRequiredMixin, ListView):
    """A view of all departments"""
    context_object_name = 'departments'
    model = Department
    permission_required = 'agreements.view_department'


class DepartmentRead(PermissionRequiredMixin, DetailView):
    """A view of a department"""
    context_object_name = 'department'
    model = Department
    permission_required = 'agreements.view_department'
    template_name_suffix = '_read'


class DepartmentCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create a department"""
    form_class = DepartmentCreateForm
    model = Department
    permission_required = 'agreements.add_department'
    success_message = '%(name)s was created successfully.'
    template_name_suffix = '_create_form'


class DepartmentCreateUnderFaculty(DepartmentCreate):
    """A view to create a department under a given faculty"""

    def get_initial(self):
        initial = super().get_initial()
        initial['faculty'] = get_object_or_404(Faculty, slug=self.kwargs['facultyslug'])
        return initial


class DepartmentUpdate(PermissionRequiredMixin, SuccessMessageIfChangedMixin, UpdateView):
    """A view to update a department"""
    context_object_name = 'department'
    form_class = DepartmentUpdateForm
    model = Department
    permission_required = 'agreements.change_department'
    success_message = '%(name)s was updated successfully.'
    template_name_suffix = '_update_form'


class DepartmentDelete(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """A view to delete a department"""
    context_object_name = 'department'
    fields = '__all__'
    model = Department
    permission_required = 'agreements.delete_department'
    success_message = '%(name)s was deleted successfully.'
    success_url = reverse_lazy('departments_list')
    template_name_suffix = '_delete_form'


# Agreements

class AgreementList(LoginRequiredMixin, ListView):
    """A view of all agreements"""
    context_object_name = 'agreements'
    model = Agreement
    ordering = 'title'
    paginate_by = 15
    template_name = 'agreements/agreement_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        return [agreement for agreement in queryset
                if (not agreement.hidden) or
                has_perm(self.request.user, 'agreements.view_agreement', agreement)]


class AgreementRead(LoginRequiredMixin, UserPassesTestMixin, FormMixin, DetailView, ProcessFormView):
    """A view of an agreement"""
    context_object_name = 'agreement'
    form_class = SignatureCreateForm
    model = Agreement
    template_name_suffix = '_read'

    def test_func(self):
        agreement = self.get_object()
        # If the agreement isn't valid to see, you have to have the right permissions.
        if agreement.valid():
            return True
        return has_perm(self.request.user, 'agreements.view_agreement', agreement)

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
        context['can_edit'] = has_perm(self.request.user, 'agreements.change_agreement', context['agreement'])
        context['can_search_signatures'] = has_perm(self.request.user,
                                                    'agreements.agreement_search_signatures',
                                                    context['agreement'])
        return context


class AgreementCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """A view to create an agreement"""
    form_class = AgreementCreateForm
    model = Agreement
    permission_required = 'agreements.add_agreement'
    success_message = '%(title)s was created successfully.'
    template_name_suffix = '_create_form'


class AgreementUpdate(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin,
                      SuccessMessageIfChangedMixin, UpdateView):
    """A view to update an agreement"""
    context_object_name = 'agreement'
    form_class = AgreementUpdateForm
    model = Agreement
    permission_required = 'agreements.change_agreement'
    success_message = '%(title)s was updated successfully.'
    template_name_suffix = '_update_form'


class AgreementDelete(LoginRequiredMixin, PermissionRequiredMixin,
                      SuccessMessageMixin, DeleteView):
    """A view to delete an agreement"""
    context_object_name = 'agreement'
    fields = '__all__'
    model = Agreement
    permission_required = 'agreements.delete_agreement'
    success_message = '%(title)s was deleted successfully.'
    success_url = reverse_lazy('agreements_list')
    template_name_suffix = '_delete_form'


class AgreementPermissions(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin, DetailView):
    """A view which reports on the permissions on this agreement"""
    context_object_name = 'agreement'
    model = Agreement
    permission_required = 'agreements.change_agreement'
    template_name = 'agreements/agreement_permissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['global_permissions'] = GroupDescription.objects.for_model_with_permissions('agreement')
        context['object_permissions'] = (GroupDescription.objects
                                         .for_object_with_groupobjectpermissions('agreement', context['agreement'].id))
        return context


class AgreementPermissionsGroups(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin, DetailView):
    """A view which lists groups"""
    context_object_name = 'agreement'
    model = Agreement
    permission_required = 'agreements.change_agreement'
    template_name = 'agreements/agreement_permissions_groups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_permissions'] = (GroupDescription.objects
                                         .for_object_with_groupobjectpermissions('agreement', context['agreement'].id))
        context['groupdescriptions'] = []
        groupdescriptions = GroupDescription.objects.all().order_by('name')
        # .difference() would be better here but it causes an error.
        for groupdescription in groupdescriptions:
            if groupdescription not in context['object_permissions']:
                context['groupdescriptions'].append(groupdescription)
        return context


class AgreementPermissionsGroupUpdate(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin,
                                      SuccessMessageIfChangedMixin, FormMixin, DetailView, ProcessFormView):
    """A view which updates the per-object permissions of an agreement for a group"""
    context_object_name = 'agreement'
    form_class = CustomGroupObjectPermissionsForm
    model = Agreement
    permission_required = 'agreements.add_agreement'
    template_name = 'agreements/agreement_permissions_group_update.html'

    def get_success_url(self):
        return reverse_lazy('agreements_permissions_groups', kwargs={'slug': self.kwargs['slug']})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'group': get_object_or_404(GroupDescription, slug=self.kwargs['groupdescriptionslug']).group,
            'obj': self.get_object(),
        })
        return kwargs

    def get_context_data(self, **kwargs):
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = super().get_context_data(**kwargs)
        context['groupdescription'] = get_object_or_404(GroupDescription, slug=self.kwargs['groupdescriptionslug'])
        return context

    def form_valid(self, form):
        form.save_obj_perms()
        return super().form_valid(form)


# Signatures

class AgreementSignatureList(LoginRequiredMixin, PermissionRequiredCheckGlobalMixin,
                             FormMixin, DetailView, MultipleObjectMixin):
    """A view to list and search through signatures of an agreement"""
    context_object_name = 'agreement'
    form_class = SignatureSearchForm
    model = Agreement
    paginate_by = 15
    permission_required = 'agreements.agreement_search_signatures'
    template_name = 'agreements/agreement_signature_list.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['search'] = self.request.GET.get('search', default='')
        return initial

    def get_context_data(self, **kwargs):  # pylint: disable=arguments-differ
        agreement = self.get_object()
        signatures = Signature.objects.filter(agreement=agreement).order_by('-signed_at')
        q_param = self.request.GET.get('search', '')
        if q_param != '':
            signatures = signatures.search(q_param)
        context = super().get_context_data(object_list=signatures, **kwargs)
        context['signatures'] = context['object_list']
        context['count_per_department'] = signatures.count_per_department()
        context['count_per_faculty'] = signatures.count_per_faculty()
        context['can_download_signatures'] = has_perm(self.request.user,
                                                      'agreements.agreement_search_signatures',
                                                      agreement)
        return context


class AgreementSignatureCSV(LoginRequiredMixin, UserPassesTestMixin, CSVExportView):
    """A view to download the signatures associated with an agreement as a CSV file"""
    fields = ('agreement__title', 'username', 'first_name',
              'last_name', 'email', 'department__name',
              'department__faculty__name', 'signed_at')
    model = Signature

    def test_func(self):
        agreement = get_object_or_404(
            Agreement, slug=self.kwargs['slug']
        )
        return has_perm(self.request.user, 'agreements.agreement_search_signatures', agreement)

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
            Agreement, slug=self.kwargs['slug']
        )
        qs = qs.filter(agreement=self.agreement)
        return qs
