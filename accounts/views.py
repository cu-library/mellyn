"""
This module defines the views provided by this application.

https://docs.djangoproject.com/en/3.0/topics/http/views/
"""

from django.contrib.auth.views import LoginView, LogoutView


class Login(LoginView):
    """A the user authentication login view"""
    template_name = 'accounts/login.html'


class Logout(LogoutView):
    """A the user authentication login view"""
    template_name = 'accounts/logout.html'
