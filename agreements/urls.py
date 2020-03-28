"""
This module defines the urls provided by this application.

https://docs.djangoproject.com/en/3.0/ref/urls/
"""

from django.urls import path

from . import views

urlpatterns = [  # pylint: disable=invalid-name
    path('agreements/', views.AgreementList.as_view(), name='agreements_list'),
    path('agreements/create/', views.AgreementCreate.as_view(), name='agreements_create'),
]
