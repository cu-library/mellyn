"""
This module defines the urls provided by this application.

https://docs.djangoproject.com/en/3.0/ref/urls/
"""

from django.urls import path

from . import views

urlpatterns = [  # pylint: disable=invalid-name
    path('staff/', views.StaffUserList.as_view(), name='staff_list'),
    path('staff/<slug:slug>/', views.StaffUserRead.as_view(), name='staff_read'),
    path('groups/', views.GroupDescriptionList.as_view(), name='groupdescriptions_list'),
    path('groups/create/', views.GroupDescriptionCreate.as_view(), name='groupdescriptions_create'),
    path('groups/<slug:slug>/', views.GroupDescriptionRead.as_view(), name='groupdescriptions_read'),
    path('groups/<slug:slug>/update/', views.GroupDescriptionUpdate.as_view(), name='groupdescriptions_update'),
    path('groups/<slug:slug>/update/permissions/',
         views.GroupDescriptionUpdatePermissions.as_view(),
         name='groupdescriptions_update_permissions'),
    path('groups/<slug:slug>/delete/', views.GroupDescriptionDelete.as_view(), name='groupdescriptions_delete'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
]
