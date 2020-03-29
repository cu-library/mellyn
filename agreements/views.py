"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.urls import reverse_lazy
from django.views import generic
from .models import Agreement


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
