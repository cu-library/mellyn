"""This module has project-level views which are not tied to any application"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views.generic import TemplateView


class IsStaffMixin(UserPassesTestMixin):
    """A custom access mixin which ensures the user is a staff member"""
    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff


class AdminView(LoginRequiredMixin, IsStaffMixin, TemplateView):
    """A view to help admin staff access lists of Models"""
    template_name = 'admin.html'


def index(request):
    """A view for the 'homepage', or root page, of the project"""
    if request.user.is_authenticated:
        return redirect('agreements_list')
    return render(request, 'index.html')
