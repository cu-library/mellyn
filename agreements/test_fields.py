"""
This module defines tests to run against the fields module.

https://docs.djangoproject.com/en/3.0/topics/testing/
"""

from django.forms import ValidationError
from django.test import TestCase

from .fields import GroupedModelChoiceField, SplitLineField
from .models import Department, Faculty


class SplitLineFieldTestCase(TestCase):
    """Tests for the SplitLineField."""

    def test_splitlinefield(self):
        """Test that input is properly processed and that duplicates raise an error"""
        field = SplitLineField()
        self.assertEqual(field.clean(' 1'), ['1'])
        self.assertEqual(field.clean('1 '), ['1'])
        self.assertEqual(field.clean('   1   \n   2\n3   \n\n\n\n\n\n4\n\n\n\n\t5\t\n\n\n6'),
                         ['1', '2', '3', '4', '5', '6'])
        with self.assertRaisesMessage(ValidationError, "1 is a duplicate line."):
            field.clean('1\n2\n3\n   1     ')


class GroupedModelChoiceFieldTestCase(TestCase):
    """Tests for the GroupedModelChoiceField/GroupedModelChoiceIterator"""

    def test_groupedmodelchoicefield(self):
        """Test to see that the choice field is grouped as expected"""
        test_faculty_1 = Faculty(name='Test Faculty One', slug='test_faculty_1')
        test_faculty_1.full_clean()
        test_faculty_1.save()
        test_faculty_2 = Faculty(name='Test Faculty Two', slug='test_faculty_2')
        test_faculty_2.full_clean()
        test_faculty_2.save()
        test_department_1 = Department(name='Test Department One', slug='test_department_1', faculty=test_faculty_1)
        test_department_1.full_clean()
        test_department_1.save()
        test_department_2 = Department(name='Test Department Two', slug='test_department_2', faculty=test_faculty_2)
        test_department_2.full_clean()
        test_department_2.save()

        field = GroupedModelChoiceField(
            label='Your Department',
            queryset=Department.objects.all(),
            choices_groupby='faculty'
        )

        expected_choices_list = [('', '---------'),
                                 ('Test Faculty One', [(1, 'Test Department One')]),
                                 ('Test Faculty Two', [(2, 'Test Department Two')])]

        self.assertEqual(expected_choices_list, list(field.choices))
