"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Agreement, Faculty, Department, Signature


class AgreementModelTestCase(TestCase):
    """Tests for the Agreement model."""
    def setUp(self):
        """Initially, create an Agreement which passes all validation."""
        self.test_agreement = Agreement(title='test-one',
                                        slug='test-one',
                                        resource='test-resource',
                                        resource_slug='test-resource',
                                        body='body',
                                        redirect_url='https://example.com',
                                        redirect_text='example-redirect')
        self.test_agreement.full_clean()
        self.test_agreement.save()

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


class FacultyModelTestCase(TestCase):
    """Tests for the Faculty model."""

    def setUp(self):
        """Initially, create an Faculty which passes all validation."""
        self.test_faculty = Faculty(name='Test', slug='test')
        self.test_faculty.full_clean()
        self.test_faculty.save()

    def test_slug_value_create(self):
        """Check that the slug value can't be 'create'"""
        with self.assertRaisesRegex(ValidationError, "The slug cannot be 'create'."):
            self.test_faculty.slug = 'create'
            self.test_faculty.full_clean()

    def test_slug_can_contain_create(self):
        """Check that the slug can contain the string 'create'"""
        self.test_faculty.slug = '123create'
        self.test_faculty.full_clean()

        self.test_faculty.slug = 'create123'
        self.test_faculty.full_clean()

        self.test_faculty.slug = '123create123'
        self.test_faculty.full_clean()


class DepartmentModelTestCase(TestCase):
    """Tests for the Department model."""

    def setUp(self):
        """Initially, create an Department which passes all validation."""
        self.test_faculty = Faculty(name='Test', slug='test')
        self.test_faculty.full_clean()
        self.test_faculty.save()
        self.test_department = Department(name='Test', slug='test', faculty=self.test_faculty)
        self.test_department.full_clean()
        self.test_department.save()

    def test_slug_value_create(self):
        """Check that the slug value can't be 'create'"""
        with self.assertRaisesRegex(ValidationError, "The slug cannot be 'create'."):
            self.test_department.slug = 'create'
            self.test_department.full_clean()

    def test_slug_can_contain_create(self):
        """Check that the slug can contain the string 'create'"""
        self.test_department.slug = '123create'
        self.test_department.full_clean()

        self.test_department.slug = 'create123'
        self.test_department.full_clean()

        self.test_department.slug = '123create123'
        self.test_department.full_clean()


class SignatureModelTestCase(TestCase):
    """Tests for the Signature model."""
    @classmethod
    def setUpTestData(cls):
        """Create a dummy agreement and user for the signatures to reference."""
        cls.test_agreement = Agreement(title='test-one',
                                       slug='test-one',
                                       resource='test-resource',
                                       resource_slug='test-resource',
                                       body='body',
                                       redirect_url='https://example.com',
                                       redirect_text='example-redirect')
        cls.test_agreement.full_clean()
        cls.test_agreement.save()
        cls.test_user = get_user_model().objects.create_user(username='test',
                                                             first_name='test',
                                                             last_name='test',
                                                             email='test@test.com',
                                                             password='testtesttest')
        cls.test_faculty = Faculty(name='Test', slug='test')
        cls.test_faculty.full_clean()
        cls.test_faculty.save()
        cls.test_department = Department(name='Test', slug='test', faculty=cls.test_faculty)
        cls.test_department.full_clean()
        cls.test_department.save()

    def setUp(self):
        """Initially, create a signature which passes all validation."""
        self.test_sig = Signature(agreement=self.test_agreement,
                                  signatory=self.test_user,
                                  first_name=self.test_user.first_name,
                                  last_name=self.test_user.last_name,
                                  user_type='test',
                                  email=self.test_user.email,
                                  department=self.test_department,
                                  banner_id=100000000)
        self.test_sig.full_clean()
        self.test_sig.save()

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


class TemplatesAndViewsTestCase(TestCase):
    """Tests for the views and templates associated with Agreements"""

    model_names = [('Agreement', 'Agreements'), ('Faculty', 'Faculties'), ('Department', 'Departments')]

    def test_common(self):
        """Check common elements of all the templates for basic CRUD actions a user can perform"""

        for singular, plural in self.model_names:
            lowercase_singular = singular.lower()
            lowercase_plural = plural.lower()

            # First, visit the list view. It should be empty.
            response = self.client.get(reverse(lowercase_plural+'_list'))
            self.assertContains(response, f'<title>Sign - {plural}</title>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<h2>{plural}</h2>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<p>No {lowercase_plural} found.</p>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<a class="ok" href="{reverse(lowercase_plural+"_create")}">'
                                          f'Create a new {lowercase_singular}</a>', msg_prefix=singular+': ', html=True)

            # Visit the create view.
            response = self.client.get(reverse(lowercase_plural+'_create'))
            self.assertContains(response, f'<title>Sign - Create a new {lowercase_singular}</title>',
                                msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<h2>Create a new {lowercase_singular}</h2>',
                                msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<a class="warning" href="{reverse(lowercase_plural+"_list")}">Cancel</a>',
                                msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<input type="submit" value="Create">', msg_prefix=singular+': ', html=True)

        test_agreement = Agreement(title='Test',
                                   slug='test',
                                   resource='test-resource',
                                   resource_slug='test-resource',
                                   body='body',
                                   redirect_url='https://example.com',
                                   redirect_text='example-redirect')
        test_agreement.full_clean()
        test_agreement.save()
        test_faculty = Faculty(name='Test', slug='test')
        test_faculty.full_clean()
        test_faculty.save()
        test_department = Department(name='Test', slug='test', faculty=test_faculty)
        test_department.full_clean()
        test_department.save()

        for singular, plural in self.model_names:
            lowercase_singular = singular.lower()
            lowercase_plural = plural.lower()

            # Visit the list view. It should now have content.
            response = self.client.get(reverse(lowercase_plural+'_list'))
            self.assertContains(response, f'<title>Sign - {plural}</title>', msg_prefix=singular+': ', html=True)
            if singular == 'Agreement':
                self.assertContains(response, f'<a href="{reverse(lowercase_plural+"_read", args=["test"])}">'
                                              f'<h3>Test</h3></a>', msg_prefix=singular+': ', html=True)
            else:
                self.assertContains(response, f'<li><a href="{reverse(lowercase_plural+"_read", args=["test"])}">'
                                              f'Test</a></li>', msg_prefix=singular+': ', html=True)

            # Visit the read view.
            response = self.client.get(reverse(lowercase_plural+'_read', args=['test']))
            self.assertContains(response, f'<title>Sign - Test</title>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<h2>Test</h2>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<a class="warning" '
                                          f'href="{reverse(lowercase_plural+"_delete", args=["test"])}">Delete</a>',
                                msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<a class="ok" '
                                          f'href="{reverse(lowercase_plural+"_update", args=["test"])}">Edit</a>',
                                msg_prefix=singular+': ', html=True)

            # Visit the update view.
            response = self.client.get(reverse(lowercase_plural+'_update', args=['test']))
            self.assertContains(response, f'<title>Sign - Update Test</title>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<h2>Update Test</h2>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<a class="warning" '
                                          f'href="{reverse(lowercase_plural+"_read", args=["test"])}">Cancel</a>',
                                msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<input type="submit" value="Save">', msg_prefix=singular+': ', html=True)

            # Visit the delete view.
            response = self.client.get(reverse(lowercase_plural+'_delete', args=['test']))
            self.assertContains(response, f'<title>Sign - Delete Test</title>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<h2>Delete Test</h2>', msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<p>Are you sure you want to delete this {lowercase_singular}?</p>',
                                msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<a class="warning" '
                                          f'href="{reverse(lowercase_plural+"_read", args=["test"])}">No</a>',
                                msg_prefix=singular+': ', html=True)
            self.assertContains(response, f'<input type="submit" value="Yes">', msg_prefix=singular+': ', html=True)
