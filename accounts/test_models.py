"""
This module defines tests to run against the fields module.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

import random
import string

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from .models import GroupDescription


class GroupDescriptionTestCase(TestCase):
    """Tests for the GroupDescription model."""

    def setUp(self):
        """Create test model instances"""
        self.test_group_description = GroupDescription(name='test-one',
                                                       slug='test-one',
                                                       description='body')
        self.test_group_description.full_clean()
        self.test_group_description.save()

    def test_slug_value_create(self):
        """Check that the slug value can't be 'create'"""
        with self.assertRaisesRegex(ValidationError, "The slug cannot be 'create'."):
            self.test_group_description.slug = 'create'
            self.test_group_description.full_clean()

    def test_slug_can_contain_create(self):
        """Check that the slug can contain the string 'create'"""
        self.test_group_description.slug = '123create'
        self.test_group_description.full_clean()

        self.test_group_description.slug = 'create123'
        self.test_group_description.full_clean()

        self.test_group_description.slug = '123create123'
        self.test_group_description.full_clean()

    def test_bleach_description(self):
        """Check that the bleach library is working."""
        self.test_group_description.description = "<script>alert('hi!');</script>"
        self.test_group_description.full_clean()
        self.test_group_description.save()
        self.assertEqual(self.test_group_description.description, "&lt;script&gt;alert('hi!');&lt;/script&gt;")

    def test_group_created_and_deleted(self):
        """Check that groups and groupdescriptions are synced"""
        test_name = 'test-'+''.join(random.choices(string.ascii_lowercase, k=10))
        test_group_description = GroupDescription(name=test_name,
                                                  slug='test-create',
                                                  description='create')
        test_group_description.full_clean()
        test_group_description.save()
        self.assertTrue(Group.objects.filter(name=test_name))
        test_group_description.delete()
        self.assertFalse(Group.objects.filter(name=test_name))

    def test_for_model_with_permissions(self):
        """Check that the for_model_with_permissions method returns the right data"""
        test_group_description_2 = GroupDescription(name='test-two',
                                                    slug='test-two',
                                                    description='body')
        test_group_description_2.full_clean()
        test_group_description_2.save()
        test_group_description_3 = GroupDescription(name='test-three',
                                                    slug='test-three',
                                                    description='body')
        test_group_description_3.full_clean()
        test_group_description_3.save()

        group_description_content_type = ContentType.objects.get_for_model(GroupDescription)
        user_content_type = ContentType.objects.get_for_model(get_user_model())

        test_permission_1 = Permission.objects.create(codename='can_test',
                                                      name='Can Test GroupDescriptions',
                                                      content_type=group_description_content_type)
        test_permission_2 = Permission.objects.create(codename='can_also_test',
                                                      name='Can Also Test GroupDescriptions',
                                                      content_type=group_description_content_type)
        test_permission_3 = Permission.objects.create(codename='can_foo_users',
                                                      name='Can Foo Users',
                                                      content_type=user_content_type)

        self.test_group_description.group.permissions.add(test_permission_1)
        self.test_group_description.group.permissions.add(test_permission_3)
        test_group_description_2.group.permissions.add(test_permission_1)
        test_group_description_2.group.permissions.add(test_permission_2)
        test_group_description_3.group.permissions.add(test_permission_3)

        groups_with_permissions = GroupDescription.objects.for_model_with_permissions('groupdescription')
        # Groups with permissions should contain groupdescription 1 and 2 but not 3.
        self.assertIn(self.test_group_description, groups_with_permissions)
        self.assertIn(test_group_description_2, groups_with_permissions)
        self.assertNotIn(test_group_description_3, groups_with_permissions)
        # GroupDescriptions should only have permissions related to the model passed in to the method.
        self.assertIn(test_permission_1, groups_with_permissions.get(name='test-one').group.permissions_on_model)
        self.assertNotIn(test_permission_3, groups_with_permissions.get(name='test-one').group.permissions_on_model)
        self.assertIn(test_permission_1, groups_with_permissions.get(name='test-two').group.permissions_on_model)
        self.assertIn(test_permission_2, groups_with_permissions.get(name='test-two').group.permissions_on_model)
        self.assertNotIn(test_permission_3, groups_with_permissions.get(name='test-one').group.permissions_on_model)
