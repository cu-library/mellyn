"""
This module defines fields used by forms in this application.

https://docs.djangoproject.com/en/3.0/ref/forms/fields/

Thanks to:
Vitor Freitas
https://simpleisbetterthancomplex.com/tutorial/2019/01/02/how-to-implement-grouped-model-choice-field.html
Simon Charette
https://code.djangoproject.com/ticket/27331
"""

from functools import partial
from itertools import groupby
from operator import attrgetter

from django.forms import CharField, Textarea, ValidationError
from django.forms.models import ModelChoiceIterator, ModelChoiceField


class SplitLineField(CharField):
    """A subclass of CharField which splits each line of input"""
    widget = Textarea

    def to_python(self, value):
        value = super().to_python(value)
        if not value:
            return []
        return list(filter(None, map(lambda x: x.strip(), value.splitlines())))

    def validate(self, value):
        super().validate(value)
        seen = []
        for code in value:
            if code in seen:
                raise ValidationError(
                    'Invalid: %(code)s is a duplicate line.',
                    code='duplicate_line_in_input',
                    params={'code': code},
                )
            seen.append(code)


class GroupedModelChoiceIterator(ModelChoiceIterator):
    """An iterator which groups items"""
    def __init__(self, field, choices_groupby):
        self.choices_groupby = choices_groupby
        super().__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, objs in groupby(queryset, self.choices_groupby):
            yield (group, [self.choice(obj) for obj in objs])


class GroupedModelChoiceField(ModelChoiceField):
    """An ModelChoiceField which groups items"""
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = attrgetter(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError('choices_groupby must either be a str or a callable accepting a single argument')
        self.iterator = partial(GroupedModelChoiceIterator, choices_groupby=choices_groupby)
        super().__init__(*args, **kwargs)
