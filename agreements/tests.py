"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Resource, Faculty, Department, Agreement


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
                self.assertContains(response, '<input type="submit" value="Create">', html=True)

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
                self.assertContains(response, '<title>Sign - Test</title>', html=True)
                self.assertContains(response, '<h2>Test</h2>', html=True)
                self.assertContains(response, f'<a class="warning" '
                                              f'href="{reverse(lowercase_plural+"_delete", args=["test"])}">Delete</a>',
                                    html=True)
                self.assertContains(response, f'<a class="ok" '
                                              f'href="{reverse(lowercase_plural+"_update", args=["test"])}">Edit</a>',
                                    html=True)

            # Visit the update view.
            response = self.client.get(reverse(lowercase_plural+'_update', args=['test']))
            with self.subTest(msg=lowercase_plural+'_update'):
                self.assertContains(response, '<title>Sign - Update Test</title>', html=True)
                self.assertContains(response, '<h2>Update Test</h2>', html=True)
                self.assertContains(response, f'<a class="warning" '
                                              f'href="{reverse(lowercase_plural+"_read", args=["test"])}">Cancel</a>',
                                    html=True)
                self.assertContains(response, '<input type="submit" value="Save">', html=True)
                self.assertContains(response, '<input type="text" name="slug" value="test" disabled id="id_slug">',
                                    html=True)

            # Visit the delete view.
            response = self.client.get(reverse(lowercase_plural+'_delete', args=['test']))
            with self.subTest(msg=lowercase_plural+'_delete'):
                self.assertContains(response, '<title>Sign - Delete Test</title>', html=True)
                self.assertContains(response, '<h2>Delete Test</h2>', html=True)
                self.assertContains(response, f'<p>Are you sure you want to delete this {lowercase_singular}?</p>',
                                    html=True)
                self.assertContains(response, f'<a class="warning" '
                                              f'href="{reverse(lowercase_plural+"_read", args=["test"])}">No</a>',
                                    html=True)
                self.assertContains(response, '<input type="submit" value="Yes">', html=True)

    def test_skip_link(self):
        """Check that the skip link is present on all templates for basic CRUD actions a user can perform"""

        def check_skip_link(response):
            # The body element's first child should be the skip link.
            self.assertContains(response, '<body>\n    <div id="skip"><a href="#main">Skip to main content</a></div>')
            # The skip link target should be valid.
            self.assertContains(response, '<main id="main">')

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
