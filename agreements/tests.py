"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import Resource, Faculty, Department, Agreement, Signature


class ResourceModelTestCase(TestCase):
    """Tests for the Resource model."""

    def setUp(self):
        """Initially, create an Resource which passes validation."""
        self.test_resource = Resource(name='Test', slug='test', description='')
        self.test_resource.full_clean()
        self.test_resource.save()

    def test_slug_value_create(self):
        """Check that the slug value can't be 'create'"""
        with self.assertRaisesRegex(ValidationError, "The slug cannot be 'create'."):
            self.test_resource.slug = 'create'
            self.test_resource.full_clean()

    def test_slug_can_contain_create(self):
        """Check that the slug can contain the string 'create'"""
        self.test_resource.slug = '123create'
        self.test_resource.full_clean()

        self.test_resource.slug = 'create123'
        self.test_resource.full_clean()

        self.test_resource.slug = '123create123'
        self.test_resource.full_clean()

    def test_bleach_body(self):
        """Check that the bleach library is working."""
        self.test_resource.description = "<script>alert('hi!');</script>"
        self.test_resource.full_clean()
        self.test_resource.save()
        self.assertEqual(self.test_resource.description, "&lt;script&gt;alert('hi!');&lt;/script&gt;")


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


class AgreementModelTestCase(TestCase):
    """Tests for the Agreement model."""

    def setUp(self):
        """Initially, create an Agreement which passes all validation."""
        self.test_resource = Resource(name='Test', slug='test', description='')
        self.test_resource.full_clean()
        self.test_resource.save()
        self.test_agreement = Agreement(title='test-one',
                                        slug='test-one',
                                        resource=self.test_resource,
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


class SignatureModelTestCase(TestCase):
    """Tests for the Signature model."""

    @classmethod
    def setUpTestData(cls):
        """Create a dummy agreement and user for the signatures to reference."""
        cls.test_resource = Resource(name='Test', slug='test', description='')
        cls.test_resource.full_clean()
        cls.test_resource.save()
        cls.test_faculty = Faculty(name='Test', slug='test')
        cls.test_faculty.full_clean()
        cls.test_faculty.save()
        cls.test_department = Department(name='Test', slug='test', faculty=cls.test_faculty)
        cls.test_department.full_clean()
        cls.test_department.save()
        cls.test_agreement = Agreement(title='test-one',
                                       slug='test-one',
                                       resource=cls.test_resource,
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

    def setUp(self):
        """Initially, create a signature which passes all validation."""
        self.test_sig = Signature(agreement=self.test_agreement,
                                  signatory=self.test_user,
                                  username=self.test_user.username,
                                  first_name=self.test_user.first_name,
                                  last_name=self.test_user.last_name,
                                  email=self.test_user.email,
                                  department=self.test_department)
        self.test_sig.full_clean()
        self.test_sig.save()

    def test_unique_signature_constraint(self):
        """Check that the same user can't sign the same agreement twice."""
        with self.assertRaisesRegex(ValidationError, 'Signature with this Agreement and Signatory already exists.'):
            new_test_sig = Signature(agreement=self.test_agreement,
                                     signatory=self.test_user,
                                     username=self.test_user.username,
                                     first_name=self.test_user.first_name,
                                     last_name=self.test_user.last_name,
                                     email=self.test_user.email,
                                     department=self.test_department)
            new_test_sig.full_clean()


class TemplatesandViewsTestCase(TestCase):
    """Tests for templates and views associated with Agreements, Faculties, and Departments"""

    model_names = [('Resource', 'Resources'), ('Faculty', 'Faculties'),
                   ('Department', 'Departments'), ('Agreement', 'Agreements'), ]

    @classmethod
    def setUpTestData(cls):
        """Create a dummy agreement and user for the signatures to reference."""
        cls.test_user = get_user_model().objects.create_superuser(username='test',
                                                                  first_name='test',
                                                                  last_name='test',
                                                                  email='test@test.com',
                                                                  password='test')

    @staticmethod
    def create_test_models():
        """Create test models, so that update and delete views can be tested"""
        test_resource = Resource(name='Test', slug='test', description='')
        test_resource.full_clean()
        test_resource.save()
        test_faculty = Faculty(name='Test', slug='test')
        test_faculty.full_clean()
        test_faculty.save()
        test_department = Department(name='Test', slug='test', faculty=test_faculty)
        test_department.full_clean()
        test_department.save()
        test_agreement = Agreement(title='Test',
                                   slug='test',
                                   resource=test_resource,
                                   body='body',
                                   redirect_url='https://example.com',
                                   redirect_text='example-redirect')
        test_agreement.full_clean()
        test_agreement.save()

    def test_crud_actions(self):
        """Sanity check all templates for basic CRUD actions a user can perform"""

        self.client.login(username='test', password='test')

        for singular, plural in self.model_names:
            lowercase_singular = singular.lower()
            lowercase_plural = plural.lower()

            # First, visit the list view. It should be empty.
            response = self.client.get(reverse(lowercase_plural+'_list'))
            with self.subTest(msg=lowercase_plural+'_list'):
                self.assertContains(response, f'<title>Sign - {plural}</title>', html=True)
                self.assertContains(response, f'<h2>{plural}</h2>', html=True)
                self.assertContains(response, f'<p>No {lowercase_plural} found.</p>', html=True)
                self.assertContains(response, f'<a class="ok" href="{reverse(lowercase_plural+"_create")}">'
                                              f'Create a new {lowercase_singular}</a>', html=True)

            # Visit the create view.
            response = self.client.get(reverse(lowercase_plural+'_create'))
            with self.subTest(msg=lowercase_plural+'_create'):
                self.assertContains(response, f'<title>Sign - Create a new {lowercase_singular}</title>',
                                    html=True)
                self.assertContains(response, f'<h2>Create a new {lowercase_singular}</h2>',
                                    html=True)
                self.assertContains(response,
                                    f'<a class="warning" href="{reverse(lowercase_plural+"_list")}">Cancel</a>',
                                    html=True)
                self.assertContains(response, f'<input type="submit" value="Create">', html=True)

        self.create_test_models()

        for singular, plural in self.model_names:
            lowercase_singular = singular.lower()
            lowercase_plural = plural.lower()

            # Visit the list view. It should now have content.
            response = self.client.get(reverse(lowercase_plural+'_list'))
            with self.subTest(msg=lowercase_plural+'_list'):
                self.assertContains(response, f'<title>Sign - {plural}</title>', html=True)
                if singular == 'Agreement':
                    self.assertContains(response, f'<a href="{reverse(lowercase_plural+"_read", args=["test"])}">'
                                                  f'<h3>Test</h3></a>', html=True)
                else:
                    self.assertContains(response, f'<li><a href="{reverse(lowercase_plural+"_read", args=["test"])}">'
                                                  f'Test</a></li>', html=True)

            # Visit the read view.
            response = self.client.get(reverse(lowercase_plural+'_read', args=['test']))
            with self.subTest(msg=lowercase_plural+'_read'):
                self.assertContains(response, f'<title>Sign - Test</title>', html=True)
                self.assertContains(response, f'<h2>Test</h2>', html=True)
                self.assertContains(response, f'<a class="warning" '
                                              f'href="{reverse(lowercase_plural+"_delete", args=["test"])}">Delete</a>',
                                    html=True)
                self.assertContains(response, f'<a class="ok" '
                                              f'href="{reverse(lowercase_plural+"_update", args=["test"])}">Edit</a>',
                                    html=True)

            # Visit the update view.
            response = self.client.get(reverse(lowercase_plural+'_update', args=['test']))
            with self.subTest(msg=lowercase_plural+'_update'):
                self.assertContains(response, f'<title>Sign - Update Test</title>', html=True)
                self.assertContains(response, f'<h2>Update Test</h2>', html=True)
                self.assertContains(response, f'<a class="warning" '
                                              f'href="{reverse(lowercase_plural+"_read", args=["test"])}">Cancel</a>',
                                    html=True)
                self.assertContains(response, f'<input type="submit" value="Save">', html=True)
                self.assertContains(response, f'<input type="text" name="slug" value="test" disabled id="id_slug">',
                                    html=True)

            # Visit the delete view.
            response = self.client.get(reverse(lowercase_plural+'_delete', args=['test']))
            with self.subTest(msg=lowercase_plural+'_delete'):
                self.assertContains(response, f'<title>Sign - Delete Test</title>', html=True)
                self.assertContains(response, f'<h2>Delete Test</h2>', html=True)
                self.assertContains(response, f'<p>Are you sure you want to delete this {lowercase_singular}?</p>',
                                    html=True)
                self.assertContains(response, f'<a class="warning" '
                                              f'href="{reverse(lowercase_plural+"_read", args=["test"])}">No</a>',
                                    html=True)
                self.assertContains(response, f'<input type="submit" value="Yes">', html=True)

    def test_skip_link(self):
        """Check that the skip link is present on all templates for basic CRUD actions a user can perform"""

        def check_skip_link(response):
            # The body element's first child should be the skip link.
            self.assertContains(response, f'<body>\n    <div id="skip"><a href="#main">Skip to main content</a></div>')
            # The skip link target should be valid.
            self.assertContains(response, f'<main id="main">')

        response = self.client.get(reverse('index'))
        with self.subTest(msg='index'):
            check_skip_link(response)

        self.client.login(username='test', password='test')

        for _, plural in self.model_names:
            lowercase_plural = plural.lower()

            response = self.client.get(reverse(lowercase_plural+'_list'))
            with self.subTest(msg=lowercase_plural+'_list'):
                check_skip_link(response)

            # Visit the create view.
            response = self.client.get(reverse(lowercase_plural+'_create'))
            with self.subTest(msg=lowercase_plural+'_create'):
                check_skip_link(response)

        self.create_test_models()

        for _, plural in self.model_names:
            lowercase_plural = plural.lower()

            # Visit the list view. It should now have content.
            response = self.client.get(reverse(lowercase_plural+'_list'))
            with self.subTest(msg=lowercase_plural+'_list'):
                check_skip_link(response)

            # Visit the read view.
            response = self.client.get(reverse(lowercase_plural+'_read', args=['test']))
            with self.subTest(msg=lowercase_plural+'_read'):
                check_skip_link(response)

            # Visit the update view.
            response = self.client.get(reverse(lowercase_plural+'_update', args=['test']))
            with self.subTest(msg=lowercase_plural+'_update'):
                check_skip_link(response)

            # Visit the delete view.
            response = self.client.get(reverse(lowercase_plural+'_delete', args=['test']))
            with self.subTest(msg=lowercase_plural+'_delete'):
                check_skip_link(response)

    def test_label_suffix(self):
        """Test to make sure the label suffix has been removed"""

        def check_label_suffix(response):
            self.assertEqual(response.context['form'].label_suffix, '')

        self.client.login(username='test', password='test')

        for _, plural in self.model_names:
            lowercase_plural = plural.lower()

            # Visit the create view.
            response = self.client.get(reverse(lowercase_plural+'_create'))
            with self.subTest(msg=lowercase_plural+'_create'):
                check_label_suffix(response)

        self.create_test_models()

        for _, plural in self.model_names:
            lowercase_plural = plural.lower()

            # Visit the update view.
            response = self.client.get(reverse(lowercase_plural+'_update', args=['test']))
            with self.subTest(msg=lowercase_plural+'_update'):
                check_label_suffix(response)
