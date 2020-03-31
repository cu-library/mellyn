"""
This module defines the urls provided by this application.

https://docs.djangoproject.com/en/3.0/ref/urls/
"""

from django.urls import path

from . import views

urlpatterns = [  # pylint: disable=invalid-name
    path('agreements/', views.AgreementList.as_view(), name='agreements_list'),
    path('agreements/create/', views.AgreementCreate.as_view(), name='agreements_create'),
    path('agreements/<slug:slug>/', views.AgreementRead.as_view(), name='agreements_read'),
    path('agreements/<slug:slug>/update/', views.AgreementUpdate.as_view(), name='agreements_update'),
    path('agreements/<slug:slug>/delete/', views.AgreementDelete.as_view(), name='agreements_delete'),
    path('faculties/', views.FacultyList.as_view(), name='faculties_list'),
    path('faculties/create/', views.FacultyCreate.as_view(), name='faculties_create'),
    path('faculties/<slug:slug>/', views.FacultyRead.as_view(), name='faculties_read'),
    path('faculties/<slug:slug>/update/', views.FacultyUpdate.as_view(), name='faculties_update'),
    path('faculties/<slug:slug>/delete/', views.FacultyDelete.as_view(), name='faculties_delete'),
    path('departments/', views.DepartmentList.as_view(), name='departments_list'),
    path('departments/create/', views.DepartmentCreate.as_view(), name='departments_create'),
    path('departments/create/partof/<slug:facultyslug>/',
         views.DepartmentCreateUnderFaculty.as_view(),
         name='departments_create_under_faculty'),
    path('departments/<slug:slug>/', views.DepartmentRead.as_view(), name='departments_read'),
    path('departments/<slug:slug>/update/', views.DepartmentUpdate.as_view(), name='departments_update'),
    path('departments/<slug:slug>/delete/', views.DepartmentDelete.as_view(), name='departments_delete'),
]
