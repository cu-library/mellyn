"""
This module defines the urls provided by this application.

https://docs.djangoproject.com/en/3.0/ref/urls/
"""

from django.urls import path

from . import views

urlpatterns = [  # pylint: disable=invalid-name
    path('staff/', views.StaffUserList.as_view(), name='staff_list'),
    path('staff/<slug:slug>/', views.StaffUserRead.as_view(), name='staff_read'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
]
