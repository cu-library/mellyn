"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Agreement, Faculty, Department, Signature
from .forms import SignatureForm


class RemoveLabelSuffixMixin():  # pylint: disable=too-few-public-methods
    """Mixin which removes the label suffix"""

    def get_context_data(self, **kwargs):  # pylint: disable=missing-function-docstring
        context = super().get_context_data(**kwargs)
        context['form'].label_suffix = ''
        return context


class ReadonlySlugMixin():  # pylint: disable=too-few-public-methods
    """Mixin which disables the slug field"""

    def get_context_data(self, **kwargs):  # pylint: disable=missing-function-docstring
        context = super().get_context_data(**kwargs)
        context['form'].fields['slug'].widget.attrs['readonly'] = True
        return context


# Agreements

class AgreementList(LoginRequiredMixin, generic.ListView):
    """A view of all Agreements"""
    model = Agreement
    context_object_name = 'agreements'


class AgreementRead(PermissionRequiredMixin, generic.edit.FormMixin, generic.DetailView, generic.edit.ProcessFormView):
    """A view of an Agreement"""
    model = Agreement
    context_object_name = 'agreement'
    template_name_suffix = '_read'
    permission_required = 'agreements.view_agreement'
    form_class = SignatureForm

    def get_success_url(self):
        return reverse_lazy('agreements_read', kwargs={'slug': self.kwargs['slug']})

    def form_valid(self, form):
        signature = form.save(commit=False)
        signature.agreement = self.get_object()
        signature.signatory =self.request.user
        signature.username = self.request.user.username
        signature.first_name = self.request.user.first_name
        signature.last_name = self.request.user.last_name
        signature.email = self.request.user.email
        signature.full_clean()
        signature.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['associated_signature'] = context['agreement'].signature_set.filter(signatory=self.request.user).get()
        except Signature.DoesNotExist:
            context['associated_signature'] = None
        return context


class AgreementCreate(PermissionRequiredMixin, RemoveLabelSuffixMixin, generic.edit.CreateView):
    """A view to create an Agreement"""
    model = Agreement
    fields = '__all__'
    template_name_suffix = '_create_form'
    permission_required = 'agreements.add_agreement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['body'].widget.attrs['data-allowed-tags'] = ','.join(Agreement.BODY_ALLOWED_TAGS)
        context['form'].fields['redirect_url'].initial = 'https://'
        return context


class AgreementUpdate(PermissionRequiredMixin, RemoveLabelSuffixMixin, ReadonlySlugMixin, generic.edit.UpdateView):
    """A view to update an Agreement"""
    model = Agreement
    fields = '__all__'
    template_name_suffix = '_update_form'
    permission_required = 'agreements.change_agreement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['resource_slug'].widget.attrs['readonly'] = True
        context['form'].fields['body'].widget.attrs['data-allowed-tags'] = ','.join(Agreement.BODY_ALLOWED_TAGS)
        return context


class AgreementDelete(PermissionRequiredMixin, generic.edit.DeleteView):
    """A view to delete an Agreement"""
    model = Agreement
    fields = '__all__'
    context_object_name = 'agreement'
    template_name_suffix = '_delete_form'
    success_url = reverse_lazy('agreements_list')
    permission_required = 'agreements.delete_agreement'


# Faculties

class FacultyList(generic.ListView):
    """A view of all Faculties"""
    model = Faculty
    context_object_name = 'faculties'


class FacultyRead(generic.DetailView):
    """A view of a Faculty"""
    model = Faculty
    context_object_name = 'faculty'
    template_name_suffix = '_read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = context['faculty'].department_set.all()
        return context


class FacultyCreate(RemoveLabelSuffixMixin, generic.edit.CreateView):
    """A view to create a Faculty"""
    model = Faculty
    fields = '__all__'
    template_name_suffix = '_create_form'


class FacultyUpdate(RemoveLabelSuffixMixin, ReadonlySlugMixin, generic.edit.UpdateView):
    """A view to update a Faculty"""
    model = Faculty
    fields = '__all__'
    template_name_suffix = '_update_form'


class FacultyDelete(generic.edit.DeleteView):
    """A view to delete a Faculty"""
    model = Faculty
    fields = '__all__'
    context_object_name = 'faculty'
    template_name_suffix = '_delete_form'
    success_url = reverse_lazy('faculties_list')


# Departments

class DepartmentList(generic.ListView):
    """A view of all Departments"""
    model = Department
    context_object_name = 'departments'


class DepartmentRead(generic.DetailView):
    """A view of a Department"""
    model = Department
    context_object_name = 'department'
    template_name_suffix = '_read'


class DepartmentCreate(RemoveLabelSuffixMixin, generic.edit.CreateView):
    """A view to create a Department"""
    model = Department
    fields = '__all__'
    template_name_suffix = '_create_form'


class DepartmentCreateUnderFaculty(RemoveLabelSuffixMixin, generic.edit.CreateView):
    """A view to create a Department under a given Faculty"""
    model = Department
    fields = '__all__'
    template_name_suffix = '_create_form'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = get_object_or_404(Faculty, slug=self.kwargs['facultyslug'])
        context['form'].fields['faculty'].initial = faculty.id
        return context


class DepartmentUpdate(RemoveLabelSuffixMixin, ReadonlySlugMixin, generic.edit.UpdateView):
    """A view to update a Department"""
    model = Department
    fields = '__all__'
    template_name_suffix = '_update_form'


class DepartmentDelete(generic.edit.DeleteView):
    """A view to delete a Department"""
    model = Department
    fields = '__all__'
    context_object_name = 'department'
    template_name_suffix = '_delete_form'
    success_url = reverse_lazy('departments_list')
