"""
This module defines tests to run against the fields module.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from datetime import datetime, timezone

from django.forms import ValidationError
from django.test import TestCase

from .forms import AgreementBaseForm


class AgreementBaseFormTestCase(TestCase):
    """Tests for the AgreementBaseForm."""

    def test_agreementbaseform_clean(self):
        """Test that the end date can't be before the start date"""
        form = AgreementBaseForm()
        form.cleaned_data = {'start': datetime(1994, 6, 9, tzinfo=timezone.utc),
                             'end': datetime(1963, 6, 19, tzinfo=timezone.utc)}
        form.clean()
        self.assertIn('"End" date and time is before "Start" date and time.', form.non_field_errors())

        form = AgreementBaseForm()
        form.cleaned_data = {'start': datetime(1999, 12, 31, tzinfo=timezone.utc),
                             'end': datetime(2000, 1, 1, tzinfo=timezone.utc)}
        form.clean()
        self.assertNotIn('"End" date and time is before "Start" date and time.', form.non_field_errors())

        form = AgreementBaseForm()
        form.cleaned_data = {'start': datetime(1999, 12, 31, tzinfo=timezone.utc),
                             'end': None}
        form.clean()
        self.assertNotIn('"End" date and time is before "Start" date and time.', form.non_field_errors())
