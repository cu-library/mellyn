"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.test import TestCase

from .apps import AccountsConfig


class AccountsConfigTestCase(TestCase):
    """Tests for this application's configuration"""
    def test_application_name(self):
        """Check that the application has the expected name"""
        accounts_app = AccountsConfig.create('accounts')
        self.assertEqual(accounts_app.name, 'accounts')
