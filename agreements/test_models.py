"""
This module defines tests to run against the fields module.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from datetime import timedelta
from unittest.mock import patch
import random

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.timezone import now

from .models import Resource, Faculty, Department, Agreement, Signature, FileDownloadEvent


class ResourceModelTestCase(TestCase):
    """Tests for the Resource model."""

    def setUp(self):
        """Create test model instances"""
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
        """Create test model instances"""
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
        """Create test model instances"""
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
        """Create test model instances"""
        self.test_faculty = Faculty(name='Test', slug='test')
        self.test_faculty.full_clean()
        self.test_faculty.save()
        self.test_department = Department(name='Test', slug='test', faculty=self.test_faculty)
        self.test_department.full_clean()
        self.test_department.save()
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

    def test_for_resource_with_signature(self):
        """
        Test that the for_resource_with_signature method of the custom queryset returns
        the right signature
        """
        test_user = get_user_model().objects.create_user(username='test',
                                                         first_name='test',
                                                         last_name='test',
                                                         email='test@test.com',
                                                         password='testtesttest')
        test_user_2 = get_user_model().objects.create_user(username='test2',
                                                           first_name='test2',
                                                           last_name='test2',
                                                           email='test2@test.com',
                                                           password='testtesttest2')
        test_sig = Signature(agreement=self.test_agreement,
                             signatory=test_user,
                             username=test_user.username,
                             first_name=test_user.first_name,
                             last_name=test_user.last_name,
                             email=test_user.email,
                             department=self.test_department)
        test_sig.full_clean()
        test_sig.save()
        test_sig_2 = Signature(agreement=self.test_agreement,
                               signatory=test_user_2,
                               username=test_user_2.username,
                               first_name=test_user_2.first_name,
                               last_name=test_user_2.last_name,
                               email=test_user_2.email,
                               department=self.test_department)
        test_sig_2.full_clean()
        test_sig_2.save()

        agreement = Agreement.objects.for_resource_with_signature(self.test_resource, test_user_2).first()
        self.assertEqual(agreement.associated_signature.username, 'test2')


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

    def test_counts(self):
        """count_per_department and count_per_faculty should return the right counts"""

        correct_count_per_faculty = {'Test': 1}
        correct_count_per_department = {'Test': 1}

        another_agreement = Agreement.objects.create(title='another',
                                                     slug='another',
                                                     resource=self. test_resource,
                                                     body='body',
                                                     redirect_url='https://example.com',
                                                     redirect_text='example-redirect')

        for faculty_iter in range(random.randint(2, 5)):
            faculty = Faculty.objects.create(name=f'Test faculty {faculty_iter}', slug=f'test{faculty_iter}')
            for dept_iter in range(random.randint(2, 5)):
                dept = Department.objects.create(name=f'Test department {faculty_iter}{dept_iter}',
                                                 slug=f'test{faculty_iter}{dept_iter}',
                                                 faculty=faculty)
                for patron_iter in range(random.randint(5, 10)):
                    user = get_user_model().objects.create_user(username=f'user{faculty_iter}{dept_iter}{patron_iter}',
                                                                first_name=f't{faculty_iter}{dept_iter}{patron_iter}',
                                                                last_name=f't{faculty_iter}{dept_iter}{patron_iter}',
                                                                email=f'{faculty_iter}{dept_iter}{patron_iter}@t.com',
                                                                password=f'{faculty_iter}{dept_iter}{patron_iter}')
                    if random.random() > 0.5:
                        Signature.objects.create(agreement=self.test_agreement,
                                                 signatory=user,
                                                 username=user.username,
                                                 first_name=user.first_name,
                                                 last_name=user.last_name,
                                                 email=user.email,
                                                 department=dept)
                        correct_count_per_faculty[faculty.name] = correct_count_per_faculty.get(faculty.name, 0) + 1
                        correct_count_per_department[dept.name] = correct_count_per_department.get(dept.name, 0) + 1
                    if random.random() > 0.5:
                        Signature.objects.create(agreement=another_agreement,
                                                 signatory=user,
                                                 username=user.username,
                                                 first_name=user.first_name,
                                                 last_name=user.last_name,
                                                 email=user.email,
                                                 department=dept)

        count_per_faculty = Signature.objects.filter(agreement=self.test_agreement).count_per_faculty()
        for count in count_per_faculty:
            self.assertEqual(count['num_sigs'], correct_count_per_faculty[count['department__faculty__name']])

        count_per_department = Signature.objects.filter(agreement=self.test_agreement).count_per_department()
        for count in count_per_department:
            self.assertEqual(count['num_sigs'], correct_count_per_department[count['department__name']])


class FileDownloadEventTestCase(TestCase):
    """Tests for the FileDownloadEvent model."""

    def setUp(self):
        """Create test model instances"""
        self.test_resource = Resource(name='Test', slug='test', description='')
        self.test_resource.full_clean()
        self.test_resource.save()

    def test_get_or_create_if_no_duplicates_past_5_minutes(self):
        """Check that get_or_create_if_no_duplicates_past_5_minutes doesn't create objects when it shouldn't."""
        FileDownloadEvent.objects.get_or_create_if_no_duplicates_past_5_minutes(self.test_resource, 'test', 'test')
        _, created = FileDownloadEvent.objects.get_or_create_if_no_duplicates_past_5_minutes(self.test_resource,
                                                                                             'test', 'test')
        self.assertFalse(created)

        now_plus_10_minutes = now()+timedelta(minutes=10)
        with patch('agreements.models.now', return_value=now_plus_10_minutes):
            _, created = FileDownloadEvent.objects.get_or_create_if_no_duplicates_past_5_minutes(self.test_resource,
                                                                                                 'test', 'test')
            self.assertTrue(created)

    def test_download_count_per_path_for_resource(self):
        """Does the download_count_per_path_for_resource method count the right number of download events?"""

        for path, count in [('test1', 1), ('test2', 2), ('test3', 3), ('test40', 40), ('testten', 10)]:
            for i in range(count):
                FileDownloadEvent.objects.create(resource=self.test_resource, path=path, session_key=f'{path}{i}')

        test_file_stats = FileDownloadEvent.objects.download_count_per_path_for_resource(self.test_resource)
        self.assertEqual({'path': 'test40', 'downloads': 40}, test_file_stats[0])
        self.assertEqual({'path': 'testten', 'downloads': 10}, test_file_stats[1])
        self.assertEqual({'path': 'test3', 'downloads': 3}, test_file_stats[2])
        self.assertEqual({'path': 'test2', 'downloads': 2}, test_file_stats[3])
        self.assertEqual({'path': 'test1', 'downloads': 1}, test_file_stats[4])
