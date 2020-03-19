"""This module has project-level views which are not tied to any application"""

from django.shortcuts import render

def index(request):
    """A view for the 'homepage', or root page, of the project"""
    return render(request, 'index.html')
