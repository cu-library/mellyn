"""
This module defines tests to run against this application.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminTestCase(TestCase):
    """Test the basic project views for redirects and access"""

    def setUp(self):
        """Create test data for this test case"""
        self.test_user = get_user_model().objects.create_user(username='test_user',
                                                              first_name='test first name',
                                                              last_name='test last name',
                                                              email='test@test.com',
                                                              password='test',
                                                              is_staff=False)

    def test_health_view(self):
        """Test the health view"""
        response = self.client.get(reverse('health'))
        self.assertContains(response, 'OK')

    def test_index_view(self):
        """Test that the index view works as expected"""

        # Before logging in, a user should see the index page.
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Please login to see ')

        # After logging in, a user should be redirected to the agreements page.
        self.client.login(username='test_user', password='test')
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('agreements_list'))

    def test_admin_view(self):
        """Only a staff user should be able to access this view"""

        self.client.login(username='test_user', password='test')

        # The user should get a 403 if they aren't a staff member.
        response = self.client.get(reverse('admin'))
        self.assertEqual(response.status_code, 403)

        # Make the user a staff member
        self.test_user.is_staff = True
        self.test_user.save()

        # The view should now be accessible
        response = self.client.get(reverse('admin'))
        self.assertContains(response, '<h2>Admin Menu</h2>', html=True)

        # Revoke staff status
        self.test_user.is_staff = False
        self.test_user.save()

        # The user should get a 403 if they aren't a staff member.
        response = self.client.get(reverse('admin'))
        self.assertEqual(response.status_code, 403)
