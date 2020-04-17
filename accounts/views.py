"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.views import generic
from django.contrib.auth.views import LoginView, LogoutView
from .models import User


class StaffUserList(generic.ListView):
    """A view of all staff users"""
    model = User
    context_object_name = 'staff'
    queryset = User.objects.filter(is_staff=True)
    template_name = 'accounts/staff_list.html'


class StaffUserRead(generic.DetailView):
    """A view of a Faculty"""
    model = User
    slug_field = 'username'
    context_object_name = 'staff_user'
    template_name = 'accounts/staff_read.html'
    queryset = User.objects.filter(is_staff=True)


class Login(LoginView):
    """A the user authentication login view"""
    template_name = 'accounts/login.html'


class Logout(LogoutView):
    """A the user authentication login view"""
    template_name = 'accounts/logout.html'
