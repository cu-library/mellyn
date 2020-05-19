"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse

from guardian.shortcuts import assign_perm, remove_perm

from .views import AgreementList, ResourceList
from .models import Resource, Faculty, Department, Agreement, Signature, LicenseCode


class SharedCRUDWorkflowsTestCase(TestCase):
    """Test CRUD workflows on resources, agreements, faculties, and departments"""

    model_names = [('Resource', 'Resources'), ('Faculty', 'Faculties'),
                   ('Department', 'Departments'), ('Agreement', 'Agreements'), ]

    @classmethod
    def setUpTestData(cls):
        """Create a super user for the tests to use."""
        cls.test_user = get_user_model().objects.create_superuser(username='test',
                                                                  first_name='test',
                                                                  last_name='test',
                                                                  email='test@test.com',
                                                                  password='test')

    @staticmethod
    def create_test_models():
        """Create test models, so that update and delete views can be tested"""
        test_resource = Resource.objects.create(name='Test', slug='test', description='')
        test_faculty = Faculty.objects.create(name='Test', slug='test')
        Department.objects.create(name='Test', slug='test', faculty=test_faculty)
        Agreement.objects.create(title='Test',
                                 slug='test',
                                 resource=test_resource,
                                 body='body',
                                 redirect_url='https://example.com',
                                 redirect_text='example-redirect')

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


class GlobalPermissionsTestCase(TestCase):
    """Test that views which only check for global permissions are correctly protected"""

    def setUp(self):
        """Create test data for this test case"""
        test_staff_1 = get_user_model().objects.create_user(username='staff1',
                                                            first_name='test',
                                                            last_name='test',
                                                            email='patron@test.com',
                                                            password='test',
                                                            is_staff=True)
        self.test_group = Group.objects.create(name='test')
        self.test_group.user_set.add(test_staff_1)
        test_resource = Resource.objects.create(name='Test resource', slug='test', description='')
        test_faculty = Faculty.objects.create(name='Test faculty', slug='test')
        Department.objects.create(name='Test department', slug='test', faculty=test_faculty)
        Agreement.objects.create(title='Test agreement',
                                 slug='test',
                                 resource=test_resource,
                                 body='body',
                                 redirect_url='https://example.com',
                                 redirect_text='example-redirect')

    def test_global_permissions(self):
        """Only a user in a group with a particular global permission should be able to access some views"""

        model_names = [('resource', 'resources'), ('faculty', 'faculties'),
                       ('department', 'departments'), ('agreement', 'agreements'), ]

        self.client.login(username='staff1', password='test')

        def check_access(action, url, perm, elem):
            """In a subtest, check the permissions on the url"""
            with self.subTest(msg=f'{url}-{perm}'):
                if action in ['read', 'update', 'delete']:
                    url_reversed = reverse(url, args=['test'])
                else:
                    url_reversed = reverse(url)
                # The staff user should get a 403 if they don't have the permission
                response = self.client.get(url_reversed)
                self.assertEqual(response.status_code, 403)

                # Give the user's group the global permission.
                permission = Permission.objects.get(codename=perm)
                self.test_group.permissions.add(permission)

                # The staff user should now see the form.
                response = self.client.get(url_reversed)
                self.assertContains(response, elem, html=True)

                # Remove the permission
                self.test_group.permissions.remove(permission)

                # The staff user should get a 403
                response = self.client.get(url_reversed)
                self.assertEqual(response.status_code, 403)

        for model, plural in model_names:
            for action, perm in [('create', 'add'), ('read', 'view'), ('update', 'change'), ('delete', 'delete')]:
                if model in ['resource', 'agreement'] and action in ['read', 'update']:
                    continue
                url = f'{plural}_{action}'
                if action == 'create':
                    check_access(action, url, f'{perm}_{model}', f'<h2>Create a new {model}</h2>')
                elif action == 'read':
                    check_access(action, url, f'{perm}_{model}', f'<h2>Test {model}</h2>')
                elif action == 'update':
                    check_access(action, url, f'{perm}_{model}', f'<h2>Update Test {model}</h2>')
                elif action == 'delete':
                    check_access(action, url, f'{perm}_{model}', f'<h2>Delete Test {model}</h2>')


class PaginationTestCase(TestCase):
    """Test pagination"""

    def setUp(self):
        """Create a test user"""
        self.user = get_user_model().objects.create_user(username='user',
                                                         first_name='test',
                                                         last_name='test',
                                                         email='admin@test.com',
                                                         password='test')

    def test_agreement_pagination(self):
        """Test agreement pagination"""
        test_resource = Resource.objects.create(name='Test', slug='test', description='')
        for i in range(35):
            Agreement.objects.create(title=f'Test-{i}',
                                     slug=f'test-{i}',
                                     resource=test_resource,
                                     body='body',
                                     redirect_url='https://example.com',
                                     redirect_text='example-redirect',
                                     hidden=((i % 10) == 0))  # 0, 10, 20, 30 are hidden
        # Test HTML
        self.client.login(username='user', password='test')
        response = self.client.get(reverse('agreements_list'))
        self.assertContains(response, '<span class="current">Page 1 of 3.</span>', html=True)
        # Test view context
        request = RequestFactory().get(reverse('agreements_list'))
        request.user = self.user
        agreement_list = AgreementList()
        agreement_list.setup(request)
        context = agreement_list.get_context_data(object_list=agreement_list.get_queryset())
        self.assertEqual(context['paginator'].count, 31)

    def test_resource_pagination(self):
        """Test resource pagination"""
        for i in range(67):
            Resource.objects.create(name=f'Test-{i}', slug=f'test-{i}', description='', hidden=((i % 10) == 0))

        # Test HTML
        self.client.login(username='user', password='test')
        response = self.client.get(reverse('resources_list'))
        self.assertContains(response, '<span class="current">Page 1 of 4.</span>', html=True)
        # Test view context
        request = RequestFactory().get(reverse('resources_list'))
        request.user = self.user
        resource_list = ResourceList()
        resource_list.setup(request)
        context = resource_list.get_context_data(object_list=resource_list.get_queryset())
        self.assertEqual(context['paginator'].count, 60)


class HiddenAgreementResourceTestCase(TestCase):
    """Test the resource and agreement listings which limit visibility of hidden objects"""

    models = ('agreement', 'resource')

    def setUp(self):
        """Create test data for this test case"""
        self.test_staff_1 = get_user_model().objects.create_user(username='staff1',
                                                                 first_name='test',
                                                                 last_name='test',
                                                                 email='staff1@test.com',
                                                                 password='test',
                                                                 is_staff=True)
        get_user_model().objects.create_user(username='staff2',
                                             first_name='test',
                                             last_name='test',
                                             email='staff2@test.com',
                                             password='test',
                                             is_staff=True)
        get_user_model().objects.create_user(username='patron',
                                             first_name='test',
                                             last_name='test',
                                             email='patron@test.com',
                                             password='test')
        self.test_group = Group.objects.create(name='test')
        self.test_resource = Resource.objects.create(name='Test Resource WooHoo', slug='test', description='')
        self.test_agreement = Agreement.objects.create(title='Test Agreement WooHoo',
                                                       slug='test',
                                                       resource=self.test_resource,
                                                       body='body',
                                                       redirect_url='https://example.com',
                                                       redirect_text='example-redirect')

        self.object_per_model = {'agreement': self.test_agreement, 'resource': self.test_resource}

    def object_visible(self, model, hidden_label=False):
        """Is the test instance of the model visible, with or without the hidden label"""
        response = self.client.get(reverse(f'{model}s_list'))
        if hidden_label:
            self.assertContains(response, f'Test {model.title()} WooHoo (Hidden)')
        else:
            self.assertContains(response, f'Test {model.title()} WooHoo')
        response = self.client.get(reverse(f'{model}s_read', args=['test']))
        self.assertContains(response, f'Test {model.title()} WooHoo')

    def object_hidden(self, model):
        """Is the test instance of the model hidden"""
        response = self.client.get(reverse(f'{model}s_list'))
        self.assertContains(response, f'<p>No {model}s found.</p>', html=True)
        self.assertNotContains(response, f'Test {model.title()} WooHoo')
        response = self.client.get(reverse(f'{model}s_read', args=['test']))
        self.assertEqual(response.status_code, 403)

    def test_object_hidden(self):
        """Test to make sure agreements and resources are hidden properly"""
        for model in self.models:
            with self.subTest(msg=model+'_test_object_hidden'):
                # Can a patron see the object before it is hidden?
                self.client.login(username='patron', password='test')
                self.object_visible(model)

                # Hide the object
                self.object_per_model[model].hidden = True
                self.object_per_model[model].save()

                # The patron should no longer be able to see the object
                self.object_hidden(model)

    def test_object_global_permissions(self):
        """Test that global group permissions allow a user to see a hidden object"""
        for model in self.models:
            with self.subTest(msg=model+'_test_agreement_global_permissions'):
                self.object_per_model[model].hidden = True
                self.object_per_model[model].save()

                # Add staff1 to the test group.
                self.test_group.user_set.add(self.test_staff_1)

                # They shouldn't be able to see the object.
                self.client.login(username='staff1', password='test')
                self.object_hidden(model)

                # Give the group the global permission.
                view_model = Permission.objects.get(codename=f'view_{model}')
                self.test_group.permissions.add(view_model)

                # They should now be able to see the agreement
                self.object_visible(model, hidden_label=True)

                # It should still be hidden for other staff members
                self.client.login(username='staff2', password='test')
                self.object_hidden(model)

    def test_per_object_permissions(self):
        """Test that object group permissions allow a user to see a hidden object"""
        for model in self.models:
            with self.subTest(msg=model+'_test_agreement_object_permissions'):
                self.object_per_model[model].hidden = True
                self.object_per_model[model].save()

                # Add staff1 to the test group.
                self.test_group.user_set.add(self.test_staff_1)

                # They shouldn't be able to see the object.
                self.client.login(username='staff1', password='test')
                self.object_hidden(model)

                # Give the group the object permission.
                assign_perm(f'view_{model}', self.test_group, self.object_per_model[model])

                # They should now be able to see the agreement
                self.object_visible(model, hidden_label=True)

                # It should still be hidden for other staff members
                self.client.login(username='staff2', password='test')
                self.object_hidden(model)


class ResourceReadTestCase(TestCase):
    """Tests for the ResourceRead view"""

    def setUp(self):
        """Create test data for this test case"""
        self.test_staff_1 = get_user_model().objects.create_user(username='staff1',
                                                                 first_name='test',
                                                                 last_name='test',
                                                                 email='staff1@test.com',
                                                                 password='test',
                                                                 is_staff=True)
        get_user_model().objects.create_user(username='patron',
                                             first_name='test',
                                             last_name='test',
                                             email='patron@test.com',
                                             password='test')
        self.test_group = Group.objects.create(name='test')
        self.test_resource = Resource.objects.create(name='Test Resource WooHoo', slug='test-resource', description='')
        self.test_agreement = Agreement.objects.create(title='Test Agreement WooHoo',
                                                       slug='test',
                                                       resource=self.test_resource,
                                                       body='body',
                                                       redirect_url='https://example.com',
                                                       redirect_text='example-redirect')
        test_faculty = Faculty.objects.create(name='Test', slug='test')
        test_department = Department.objects.create(name='Test', slug='test', faculty=test_faculty)
        test_signature = Signature.objects.create(agreement=self.test_agreement,
                                                  signatory=self.test_staff_1,
                                                  username=self.test_staff_1.username,
                                                  email=self.test_staff_1.email,
                                                  department=test_department)
        LicenseCode.objects.create(resource=self.test_resource,
                                   code='abc',
                                   signature=test_signature)

    def test_resource_associated_agreement_signature(self):
        """Test that the resource read page has the associated agreement, signature, and license code"""
        self.client.login(username='staff1', password='test')
        response = self.client.get(reverse('resources_read', args=[self.test_resource.slug]))

        # The staff member should see the associated agreement.
        self.assertContains(response, "<h3>Test Agreement WooHoo</h3>", html=True)
        # ... the associated signature
        self.assertContains(response, "You signed this agreement on ")
        # ... the associated license code
        self.assertContains(response, "<p>License Code: abc</p>", html=True)

        # Hide the agreement
        self.test_agreement.hidden = True
        self.test_agreement.save()

        response = self.client.get(reverse('resources_read', args=[self.test_resource.slug]))
        # The staff member should not see the associated agreement.
        self.assertNotContains(response, "<h3>Test Agreement WooHoo</h3>", html=True)
        # ... the associated signature
        self.assertNotContains(response, "You signed this agreement on ")
        # ... the associated license code
        self.assertNotContains(response, "<p>License Code: abc</p>", html=True)

        # Add staff1 to the test group.
        self.test_group.user_set.add(self.test_staff_1)
        # Give the group the object permission.
        assign_perm('view_agreement', self.test_group, self.test_agreement)

        response = self.client.get(reverse('resources_read', args=['test-resource']))
        # The staff member should now see the associated agreement.
        self.assertContains(response, "<h3>Test Agreement WooHoo (Hidden)</h3>", html=True)
        # ... the associated signature
        self.assertContains(response, "You signed this agreement on ")
        # ... the associated license code
        self.assertContains(response, "<p>License Code: abc</p>", html=True)

    def test_actions_respect_permissions(self):
        """Test that the actions which require edit permissions don't appear if you don't have those permissions"""

        permissions_action_html = ('<a class="permissions" '
                                   f"href=\"{reverse('resources_permissions', args=[self.test_resource.slug])}\""
                                   '>Permissions</a>')

        edit_action_html = ('<a class="ok" '
                            f"href=\"{reverse('resources_update', args=[self.test_resource.slug])}\""
                            '>Edit</a>')

        file_access_stats_action_html = ('<a class="bonus" '
                                         f"href=\"{reverse('resources_file_stats', args=[self.test_resource.slug])}\""
                                         '>File Access Stats</a>')

        licensecodes_action_html = ('<a class="bonus" '
                                    f"href=\"{reverse('resources_codes_list', args=[self.test_resource.slug])}\""
                                    '>License Codes</a>')

        permissions_to_html = [('change_resource', (permissions_action_html, edit_action_html)),
                               ('resource_view_file_access_stats', (file_access_stats_action_html,)),
                               ('resource_view_licensecodes', (licensecodes_action_html,))]

        def actions_visibility(elems, visible=True):
            response = self.client.get(reverse('resources_read', args=['test-resource']))
            for elem in elems:
                if visible:
                    self.assertContains(response, elem, html=True)
                else:
                    self.assertNotContains(response, elem, html=True)

        self.test_group.user_set.add(self.test_staff_1)
        self.client.login(username='staff1', password='test')

        for permission_codename, elems in permissions_to_html:
            with self.subTest(msg=permission_codename):
                # The actions should not be available.
                actions_visibility(elems, False)

                # Give the user's group the global permission.
                permission = Permission.objects.get(codename=permission_codename)
                self.test_group.permissions.add(permission)

                # The actions should be available.
                actions_visibility(elems, True)

                # Remove the permission
                self.test_group.permissions.remove(permission)

                # The actions should not be available.
                actions_visibility(elems, False)

                # Give the user's group the object permission.
                assign_perm(permission_codename, self.test_group, self.test_resource)

                # The actions should be available.
                actions_visibility(elems, True)

                # Remove the permission
                remove_perm(permission_codename, self.test_group, self.test_resource)

                # The actions should not be available.
                actions_visibility(elems, False)
