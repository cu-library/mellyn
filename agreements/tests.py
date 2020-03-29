"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Agreement, Faculty, Department, Signature


class AgreementTestCase(TestCase):
    """Tests for the agreement model."""
    def setUp(self):
        """Initially, create an Agreement which passes all validation."""
        self.test_agreement = Agreement.objects.create(title='test-one',
                                                       slug='test-one',
                                                       resource='test-resource',
                                                       resource_slug='test-resource',
                                                       body='body',
                                                       redirect_url='https://example.com',
                                                       redirect_text='example-redirect')

    def test_bleach_body(self):
        """Check that the bleach library is working."""
        self.test_agreement.body = "<script>alert('hi!');</script>"
        self.test_agreement.full_clean()
        self.test_agreement.save()
        self.assertEqual(self.test_agreement.body, "&lt;script&gt;alert('hi!');&lt;/script&gt;")

    def test_redirect_url_https(self):
        """Check that redirect urls always use the https scheme."""
        with self.assertRaisesRegex(ValidationError, 'Enter a valid URL'):
            self.test_agreement.redirect_url = 'http://example.com'
            self.test_agreement.full_clean()

    def test_slug_value_create(self):
        """Check that the slug value can't be 'create'"""
        with self.assertRaisesRegex(ValidationError, "The slug cannot be 'create'."):
            self.test_agreement.slug = 'create'
            self.test_agreement.full_clean()

    def test_slug_can_contain_create(self):
        """Check that the slug can contain the string 'create'"""
        self.test_agreement.slug = '123create'
        self.test_agreement.full_clean()

        self.test_agreement.slug = 'create123'
        self.test_agreement.full_clean()

        self.test_agreement.slug = '123create123'
        self.test_agreement.full_clean()


class SignatureTestCase(TestCase):
    """Tests for the signature model."""
    @classmethod
    def setUpTestData(cls):
        """Create a dummy agreement and user for the signatures to reference."""
        cls.test_agreement = Agreement.objects.create(title='test-one',
                                                      slug='test-one',
                                                      resource='test-resource',
                                                      resource_slug='test-resource',
                                                      body='body',
                                                      redirect_url='https://example.com',
                                                      redirect_text='example-redirect')
        cls.test_user = get_user_model().objects.create_user(username='test',
                                                             first_name='test',
                                                             last_name='test',
                                                             email='test@test.com',
                                                             password='testtesttest')
        cls.test_faculty = Faculty.objects.create(name='Test')
        cls.test_department = Department.objects.create(name='Test', faculty=cls.test_faculty)

    def setUp(self):
        """Initially, create a signature which passes all validation."""
        self.test_sig = Signature.objects.create(agreement=self.test_agreement,
                                                 signatory=self.test_user,
                                                 first_name=self.test_user.first_name,
                                                 last_name=self.test_user.last_name,
                                                 user_type='test',
                                                 email=self.test_user.email,
                                                 department=self.test_department,
                                                 banner_id=100000000)

    def test_banner_id_validation_min(self):
        """Check that creating a signature with a Banner ID below min fails."""

        with self.assertRaisesRegex(ValidationError, 'Incorrect Banner ID Number'):
            self.test_sig.banner_id -= 1
            self.test_sig.full_clean()

    def test_banner_id_validation_max(self):
        """Check that creating a signature with a Banner ID above max fails."""

        with self.assertRaisesRegex(ValidationError, 'Incorrect Banner ID Number'):
            self.test_sig.banner_id += 100000000
            self.test_sig.full_clean()
