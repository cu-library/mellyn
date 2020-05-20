"""
This module defines tests to run against the fields module.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

import random
import string

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from guardian.shortcuts import assign_perm

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
        test_group_description_2 = GroupDescription.objects.create(name='test-two',
                                                                   slug='test-two',
                                                                   description='body')

        test_group_description_3 = GroupDescription.objects.create(name='test-three',
                                                                   slug='test-three',
                                                                   description='body')

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

    def test_for_object_with_groupobjectpermissions(self):
        """Check that the for_object_with_groupobjectpermissions method returns the right data"""

        test_group_description_2 = GroupDescription.objects.create(name='test-two',
                                                                   slug='test-two',
                                                                   description='body')

        test_group_description_3 = GroupDescription.objects.create(name='test-three',
                                                                   slug='test-three',
                                                                   description='body')

        group_description_content_type = ContentType.objects.get_for_model(GroupDescription)

        test_permission_1 = Permission.objects.create(codename='can_test',
                                                      name='Can Test GroupDescriptions',
                                                      content_type=group_description_content_type)
        test_permission_2 = Permission.objects.create(codename='can_also_test',
                                                      name='Can Also Test GroupDescriptions',
                                                      content_type=group_description_content_type)
        test_permission_3 = Permission.objects.create(codename='can_also_also_test',
                                                      name='Can Also Also Test GroupDescriptions',
                                                      content_type=group_description_content_type)

        # Assign per-object group permissions
        # 1 has all permisions on all other groups.
        assign_perm(test_permission_1.codename, self.test_group_description.group, self.test_group_description)
        assign_perm(test_permission_1.codename, self.test_group_description.group, test_group_description_2)
        assign_perm(test_permission_1.codename, self.test_group_description.group, test_group_description_3)
        assign_perm(test_permission_2.codename, self.test_group_description.group, self.test_group_description)
        assign_perm(test_permission_2.codename, self.test_group_description.group, test_group_description_2)
        assign_perm(test_permission_2.codename, self.test_group_description.group, test_group_description_3)
        assign_perm(test_permission_3.codename, self.test_group_description.group, self.test_group_description)
        assign_perm(test_permission_3.codename, self.test_group_description.group, test_group_description_2)
        assign_perm(test_permission_3.codename, self.test_group_description.group, test_group_description_3)
        # 2 has only perm 2 on groups 2 and 3.
        assign_perm(test_permission_2.codename, test_group_description_2.group, test_group_description_2)
        assign_perm(test_permission_2.codename, test_group_description_2.group, test_group_description_3)
        # 3 only has perm 3 on itself.
        assign_perm(test_permission_3.codename, test_group_description_3.group, test_group_description_3)

        # Assign a global permission
        test_group_description_2.group.permissions.add(test_permission_1)

        # Check for_object_with_groupobjectpermissions for test_group_description_3
        group_descriptions_3 = (GroupDescription.objects
                                .for_object_with_groupobjectpermissions('groupdescription',
                                                                        test_group_description_3.id))
        # All groups have some permission(s) on test_group_description_3
        self.assertIn(self.test_group_description, group_descriptions_3)
        self.assertIn(test_group_description_2, group_descriptions_3)
        self.assertIn(test_group_description_3, group_descriptions_3)
        # Test group 1 has all three permissions on test group 3
        self.assertTrue(all([perm in [gop.permission for gop in
                                      group_descriptions_3.get(name='test-one').group.groupobjectpermissions_on_object]
                             for perm in [test_permission_1,
                                          test_permission_2,
                                          test_permission_3]]))
        # Test group 2 only has permission 2 on test group 3 (which double checks that the global perm is ignored)
        permissions_list = [gop.permission for gop in
                            group_descriptions_3.get(name='test-two').group.groupobjectpermissions_on_object]
        self.assertEqual(permissions_list, [test_permission_2])

        # Check for_object_with_groupobjectpermissions for test_group_description_1
        group_descriptions_1 = (GroupDescription.objects
                                .for_object_with_groupobjectpermissions('groupdescription',
                                                                        self.test_group_description.id))
        # Only group 1 has permissions on itself
        self.assertIn(self.test_group_description, group_descriptions_1)
        self.assertNotIn(test_group_description_2, group_descriptions_1)
        self.assertNotIn(test_group_description_3, group_descriptions_1)
        # It has all three permissions
        permissions_list = [gop.permission for gop in
                            group_descriptions_1.first().group.groupobjectpermissions_on_object]
        self.assertEqual(permissions_list, [test_permission_1, test_permission_2, test_permission_3])
        # The GroupObjectPermissions objects all have the right object pk and content type model
        for gop in group_descriptions_1.first().group.groupobjectpermissions_on_object:
            self.assertEqual(int(gop.object_pk), self.test_group_description.id)  # Why is object_pk a string?
            self.assertEqual(gop.content_type.model, 'groupdescription')
