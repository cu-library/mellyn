"""This module has project-level views which are not tied to any application"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views.generic import TemplateView


class AdminView(UserPassesTestMixin, TemplateView):
    """A view to help admin staff access lists of Models"""
    template_name = 'admin.html'

    def test_func(self):
        return self.request.user.is_staff


def index(request):
    """A view for the 'homepage', or root page, of the project"""
    if request.user.is_authenticated:
        return redirect('agreements_list')
    return render(request, 'index.html')
