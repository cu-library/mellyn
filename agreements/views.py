"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import get_object_or_404
from .models import Agreement, Faculty, Department


# Agreements

class AgreementList(generic.ListView):
    """A view of all Agreements"""
    model = Agreement
    context_object_name = 'agreements'


class AgreementRead(generic.DetailView):
    """A view of an Agreement"""
    model = Agreement
    context_object_name = 'agreement'
    template_name_suffix = '_read'


class AgreementCreate(generic.edit.CreateView):
    """A view to create an Agreement"""
    model = Agreement
    fields = '__all__'
    template_name_suffix = '_create_form'


class AgreementUpdate(generic.edit.UpdateView):
    """A view to update an Agreement"""
    model = Agreement
    fields = '__all__'
    template_name_suffix = '_update_form'


class AgreementDelete(generic.edit.DeleteView):
    """A view to delete an Agreement"""
    model = Agreement
    fields = '__all__'
    context_object_name = 'agreement'
    template_name_suffix = '_delete_form'
    success_url = reverse_lazy('agreements_list')


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


class FacultyCreate(generic.edit.CreateView):
    """A view to create a Faculty"""
    model = Faculty
    fields = '__all__'
    template_name_suffix = '_create_form'


class FacultyUpdate(generic.edit.UpdateView):
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


class DepartmentCreate(generic.edit.CreateView):
    """A view to create a Department"""
    model = Department
    fields = '__all__'
    template_name_suffix = '_create_form'


class DepartmentCreateUnderFaculty(generic.edit.CreateView):
    """A view to create a Department under a given Faculty"""
    model = Department
    fields = '__all__'
    template_name_suffix = '_create_form'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = get_object_or_404(Faculty, slug=self.kwargs['facultyslug'])
        context['form'].fields['faculty'].initial = faculty.id
        return context


class DepartmentUpdate(generic.edit.UpdateView):
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
