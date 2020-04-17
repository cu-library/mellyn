"""This module has project-level views which are not tied to any application"""

from django.shortcuts import render, redirect


def index(request):
    """A view for the 'homepage', or root page, of the project"""
    if request.user.is_authenticated:
        return redirect('agreements_list')
    return render(request, 'index.html')
