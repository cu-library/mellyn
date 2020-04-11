"""
This module defines any custom forms used by this application.

https://docs.djangoproject.com/en/3.0/topics/forms/
"""

from django import forms
from django.forms import ModelForm
from .models import Signature


class SignatureForm(ModelForm):
    """A custom ModelForm for Signatures"""

    sign = forms.BooleanField(label='I have read and accepted this agreement', label_suffix='')

    class Meta:
        model = Signature
        fields = ['sign', 'department']
        labels = {'department': 'Your Department'}
