"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import GroupDescription


class PermissionsTestCase(TestCase):
    """Test that views are properly protected by permissions checking"""

    def setUp(self):
        """Create test data for this test case"""
        self.test_user = get_user_model().objects.create_user(username='test_user',
                                                              first_name='test first name',
                                                              last_name='test last name',
                                                              email='test@test.com',
                                                              password='test',
                                                              is_staff=False)
        self.test_group_description = GroupDescription.objects.create(name='test-one',
                                                                      slug='test-one',
                                                                      description='body')
        self.test_group_description.group.user_set.add(self.test_user)

    def test_user_views(self):
        """Only a staff user should be able to access these views"""

        self.client.login(username='test_user', password='test')

        for url in [reverse('users_list'),
                    reverse('users_read', args=[self.test_user.username]),
                    reverse('users_update', args=[self.test_user.username])]:
            with self.subTest(msg=url):
                # The user should get a 403 if they aren't a staff member.
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

                # Make the user a staff member
                self.test_user.is_staff = True
                self.test_user.save()

                # The view should now be accessible
                response = self.client.get(url)
                self.assertContains(response, f'{self.test_user.first_name} {self.test_user.last_name}')

                # Revoke staff status
                self.test_user.is_staff = False
                self.test_user.save()

                # The user should get a 403 if they aren't a staff member.
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_groupdescription_views(self):
        """Only a user with the right permissions should be able to access these views"""

        self.client.login(username='test_user', password='test')

        for url, perm, elem in [(reverse('groupdescriptions_list'),
                                 'view_groupdescription',
                                 '<h2>Groups</h2>'),
                                (reverse('groupdescriptions_read', args=['test-one']),
                                 'view_groupdescription',
                                 '<h2>test-one</h2>'),
                                (reverse('groupdescriptions_create'),
                                 'add_groupdescription',
                                 '<h2>Create a new group</h2>'),
                                (reverse('groupdescriptions_update', args=['test-one']),
                                 'change_groupdescription',
                                 '<h2>Update test-one</h2>'),
                                (reverse('groupdescriptions_update_permissions', args=['test-one']),
                                 'change_groupdescription',
                                 '<h2>Update permissions for test-one</h2>'),
                                (reverse('groupdescriptions_delete', args=['test-one']),
                                 'delete_groupdescription',
                                 '<h2>Delete test-one</h2>')]:
            with self.subTest(msg=f'{url}-{perm}-{elem}'):
                # The user should be denied access without the permission
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

                # Give the user's group the global permission.
                permission = Permission.objects.get(codename=perm)
                self.test_group_description.group.permissions.add(permission)

                # The user should now see the form.
                response = self.client.get(url)
                self.assertContains(response, elem, html=True)

                # Remove the permission
                self.test_group_description.group.permissions.remove(permission)

                # The user should get a 403
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
