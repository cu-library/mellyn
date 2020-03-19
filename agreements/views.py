"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.views import generic
from .models import Agreement


class AgreementList(generic.ListView):
    """A view of all the agreements in the database"""
    model = Agreement
    context_object_name = 'agreements'
