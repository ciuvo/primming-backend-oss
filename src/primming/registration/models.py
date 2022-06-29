# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from datetime import datetime
from math import log10
from typing import Any
from typing import Mapping
from typing import Type

from django import forms
from django.conf import settings
from django.db import models
from django.db import transaction
from django.forms import Form
from django.utils.timezone import now as django_now
from django.utils.translation import gettext_lazy

from primming.registration.fields import ConditionalMultiValueField
from primming.registration.widgets import ConditionalMultiField


class TypeConversionValue(models.Model):
    """
    Abstract base class for models with an attribute "value" where it isn't clear wether it is a
    string, int, or boolean (think a Persons name, age and registration status) but we still want
    to be able to use the "value" in the same manner for the most part.
    """

    # list of supported value type
    class ValueType(models.IntegerChoices):
        BOOLEAN = 1, gettext_lazy("Boolean")
        INTEGER = 2, gettext_lazy("Integer")
        FLOAT = 3, gettext_lazy("Float")
        STRING = 4, gettext_lazy("String")
        EMAIL = 5, gettext_lazy("EMail")

    # map the value type to the field name and expected type
    VALUETYPE_FIELDNAME_LOOKUP = {
        ValueType.BOOLEAN: ("value_bool", bool, forms.BooleanField),
        ValueType.INTEGER: ("value_int", int, forms.IntegerField),
        ValueType.FLOAT: ("value_float", float, forms.FloatField),
        ValueType.STRING: ("value_string", str, forms.CharField),
        ValueType.EMAIL: ("value_string", str, forms.EmailField),
    }

    value_type = models.SmallIntegerField(
        choices=ValueType.choices, default=ValueType.INTEGER, db_index=True
    )
    value_bool = models.BooleanField(null=True, blank=True, default=None, db_index=True)
    value_int = models.IntegerField(null=True, blank=True, default=None, db_index=True)
    value_float = models.FloatField(null=True, blank=True, default=None, db_index=True)
    value_string = models.CharField(
        null=True, blank=True, default=None, db_index=True, max_length=255
    )
    value_max = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        help_text="If the type of the value is a float or integer then this is the maximum value."
        "If it is a string, then it is the maximum length. Ignored for boolean types.",
    )
    value_min = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        help_text="If the type of the value is a float or integer then this is the minimum value."
        "If it is a string, then it is the minimum length. Ignored for boolean types.",
    )

    def __str__(self):
        return "{}(type:{}, range: {}-{}, b:{} i:{}: f:{}, s:{})".format(
            self.__class__.__name__,
            self.value_type,
            self.value_min,
            self.value_max,
            self.value_bool,
            self.value_int,
            self.value_float,
            self.value_string,
        )

    @property
    def value(self):
        """Get the value from the field corresponding to `value_type`
        :return: the value
        """
        return getattr(self, self.VALUETYPE_FIELDNAME_LOOKUP[self.value_type][0])

    @value.setter
    def value(self, value):
        """Store the value in the field defined by the `value_type`.

        Let django worry about the type checks, we only do range checks with `value_max` and
        `value_min`.
        """
        self._test_value_range(value)
        return setattr(self, self.VALUETYPE_FIELDNAME_LOOKUP[self.value_type][0], value)

    def _test_value_range(self, value):
        """
        test if the value passes the range constraints set by (`value_max` and `value_min`)
        :param value: the value to set on the object
        """
        if self.value_type in (self.ValueType.INTEGER, self.ValueType.FLOAT):
            # Range checks for float and int
            if self.value_max is not None and value > self.value_max:
                raise ValueError(
                    gettext_lazy("Value %s exceeds limit of %s") % (value, self.value_max)
                )
            if self.value_min is not None and value < self.value_min:
                raise ValueError(
                    gettext_lazy("Value %s is below limit of %s") % (value, self.value_min)
                )
        elif self.value_type == self.ValueType.STRING:
            # Range check of string length
            if self.value_max is not None and len(value) > self.value_max:
                raise ValueError(
                    gettext_lazy("'%s': length exceeds limit of %s") % (value, self.value_max)
                )
            if self.value_min is not None and len(value) < self.value_min:
                raise ValueError(
                    gettext_lazy("'%s': length is below limit of %s") % (value, self.value_min)
                )

    class Meta:
        abstract = True


class DynamicForm(models.Model):
    """A dynamic form with has an number of attributes type sets"""

    name = models.CharField(unique=True, max_length=100)
    display_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name used to render the form, if " "blank `name` will be used instead.",
    )
    default = models.BooleanField(null=False, default=False, unique=True)

    def save(self, *args, **kwargs):

        # make sure that there is only one default
        if self.default:
            if self.id:
                DynamicForm.objects.exclude(id=self.id).update(default=False)
            else:
                DynamicForm.objects.update(default=False)

        super().save(*args, **kwargs)

    def get_all_fields(self):
        return FieldDefinition.objects.filter(fieldsets__forms=self)

    def display_name_or_name(self) -> str:
        return self.display_name if self.display_name is not None else self.name

    def __str__(self):
        return "{}({}:{})".format(self.__class__.__name__, self.name, self.default)


class FormFieldSet(models.Model):
    """A collection of attribute types.

    Allows grouping of fields in dynamic forms
    """

    name = models.CharField(blank=True, null=True, max_length=100)
    display_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name used to render the form, if " "blank `name` will be used instead.",
    )
    forms = models.ManyToManyField(
        to=DynamicForm, through="FieldSetOrder", related_name="fieldsets"
    )

    def display_name_or_name(self) -> str:
        return self.display_name if self.display_name is not None else self.name

    def __str__(self):
        return "{}({}:{})".format(self.__class__.__name__, self.id, self.name)


class FieldSetOrder(models.Model):
    """The "through" model for the :py:class:`DynamicForm`_ <-> :py:class:`FormFieldSet`_ m2m
    relation. Holds the position of the formset in the form."""

    position = models.SmallIntegerField(
        blank=False, default=0, help_text="the position of the" "fieldset in the form"
    )
    form = models.ForeignKey(to=DynamicForm, on_delete=models.CASCADE)
    fieldset = models.ForeignKey(to=FormFieldSet, on_delete=models.CASCADE)

    def __str__(self):
        return "{}(form:{}, set:{}, pos:{}".format(
            self.__class__.__name__,
            self.form_id,
            self.fieldset_id,
            self.position,
        )


class DefaultValue(TypeConversionValue):
    """
    Default values for field definitions
    """


class FieldDefinition(models.Model):
    """
    Model to specify the type of an attribute, think "age", "gender" as the type of attribute.

    Type and range checks are specified via the set of related `allowed_attibute_values` field.
    """

    # list of supported value type
    class Widgets(models.IntegerChoices):
        AUTO = 0, "Auto"
        RADIO_BUTTONS = 1, "Radio Buttons"
        CONTIDIONAL_MULTI_FIELD = 2, "Conditional Multi Field"
        MULTICHOICE_CHECKBOXES = 3, "Multiple Choice"
        TEXT_AREA = 4, "Text area"

    WIDGET_TYPE_MAP = {
        Widgets.RADIO_BUTTONS: forms.RadioSelect,
        Widgets.CONTIDIONAL_MULTI_FIELD: ConditionalMultiField,
        Widgets.MULTICHOICE_CHECKBOXES: forms.CheckboxSelectMultiple,
        Widgets.TEXT_AREA: forms.Textarea,
    }

    name = models.CharField(
        blank=False,
        max_length=100,
        db_index=True,
        unique=True,
        help_text="Internal name for the field, e.g. 'age'",
    )
    widget = models.SmallIntegerField(
        choices=Widgets.choices,
        default=Widgets.AUTO,
        null=False,
        help_text="how to render the field",
    )
    display_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name used to render the form, if " "blank `name` will be used instead.",
    )
    fieldsets = models.ManyToManyField(to=FormFieldSet, through="FieldDefinitionOrder")

    default_value = models.ForeignKey(
        to=DefaultValue, on_delete=models.SET_DEFAULT, null=True, default=None, blank=True
    )

    def is_allowed_value(self, value: Any) -> bool:
        """If any of the related `py:class:primming.registration.models.ValueMatch`
        matches, then this is an allowed value"""
        return self.get_value_match(value) is not None

    def is_multi_value_field(self) -> bool:
        """ """
        return self.widget in (
            self.Widgets.CONTIDIONAL_MULTI_FIELD,
            self.Widgets.MULTICHOICE_CHECKBOXES,
        )

    def get_value_match(self, value: Any) -> "ValueMatch":
        """return the first value match which matches the given 'value'."""
        for allowed_value in self.allowed_values.all():
            if allowed_value.value_matches(value):
                return allowed_value
        return None

    @property
    def choices(self):
        """if the attribute type is setup with choices, get the choices"""
        for allowed_value in self.allowed_values.all():
            if allowed_value.value:
                yield allowed_value.value

    def coerce_value(self, value):
        """for parsing form inputs, how to coerce the given value into the correct type"""
        coerce = ValueMatch.VALUETYPE_FIELDNAME_LOOKUP[self.allowed_values.first().value_type][1]
        return coerce(value)

    def display_name_or_name(self) -> str:
        return self.display_name if self.display_name is not None else self.name

    def form_fieldclass(self) -> Type:
        """:return: the type for the form field"""
        values_ = self.allowed_values.all()
        multiple_values = len(values_) > 1

        if self.widget == self.Widgets.CONTIDIONAL_MULTI_FIELD:
            return ConditionalMultiValueField
        elif self.widget == self.Widgets.MULTICHOICE_CHECKBOXES:
            return forms.TypedMultipleChoiceField

        if multiple_values:
            return forms.TypedChoiceField
        else:
            allowed_value = values_.first()
            type_ = allowed_value.value_type
            return TypeConversionValue.VALUETYPE_FIELDNAME_LOOKUP[type_][2]

    def _form_field_limits(self, value_: TypeConversionValue) -> Mapping[str, str]:
        """

        :param value_:
        :return:
        """
        keywords = {}
        type_ = value_.value_type

        if type_ in (
            TypeConversionValue.ValueType.INTEGER,
            TypeConversionValue.ValueType.FLOAT,
        ):
            if value_.value_min is not None:
                keywords["min_value"] = value_.value_min
            if value_.value_max is not None:
                keywords["max_value"] = value_.value_max

        if type_ in (TypeConversionValue.ValueType.STRING,):
            if value_.value_min is not None:
                keywords["min_length"] = value_.value_min
            if value_.value_max is not None:
                keywords["max_length"] = value_.value_max
        return keywords

    def form_fieldkw(self, fieldset: FormFieldSet, klass: forms.Field) -> Mapping[str, Any]:
        """
        :return: the keywords to initialize the form field
        """
        fdo = self.fielddefinitionorder_set.get(fieldset=fieldset)
        keywords = {
            "required": not fdo.optional,
            "label": gettext_lazy(self.display_name_or_name()),
        }

        values_ = self.allowed_values.all()
        multiple_values = len(values_) > 1

        if multiple_values:
            keywords["choices"] = [
                (v.value, v.display_name if v.display_name else v.value) for v in values_
            ]

            if issubclass(klass, (forms.TypedMultipleChoiceField, forms.TypedChoiceField)):
                keywords["coerce"] = self.coerce_value
        else:
            keywords.update(self._form_field_limits(values_.first()))

        if self.widget != self.Widgets.AUTO:
            keywords["widget"] = self.WIDGET_TYPE_MAP[self.widget]

        return keywords

    def to_form_field(self, fieldset: FormFieldSet) -> forms.Field:
        """

        :param fieldset:
        :return:
        """
        klass = self.form_fieldclass()
        keywords = self.form_fieldkw(fieldset, klass)
        field = klass(**keywords)

        # add classes
        data_attrs = {"data-{}".format(a.type.name): a.value for a in self.dataattribute_set.all()}
        field.widget.attrs.update(data_attrs)

        # add size based on min/max
        if "max_length" in keywords:
            field.widget.attrs.update({"size": str(keywords["max_length"] + 3)})
        elif "max_value" in keywords:
            field.widget.attrs.update({"size": str(int(log10(keywords["max_value"])) + 2)})

        return field

    def __str__(self):
        return "{}({}:{}:{})".format(
            self.__class__.__name__, self.id, self.name, self.display_name
        )


class DataAttributeType(models.Model):
    """
    For input elements we allow optional data-XXXXX-XXX attributes. This is the model for the types
    of data-attributes.
    """

    name = models.CharField(
        blank=False,
        max_length=100,
        db_index=True,
        help_text="Name of the data-**** attribute",
    )

    def __str__(self):
        return "{}-{}".format(self.id, self.name)


class DataAttribute(models.Model):
    """
    Custom classes for
    """

    type = models.ForeignKey(DataAttributeType, on_delete=models.CASCADE)

    value = models.CharField(
        blank=False,
        max_length=100,
        db_index=True,
        help_text="Name of the HTML class",
    )

    field_definition = models.ForeignKey(to=FieldDefinition, on_delete=models.CASCADE)


class FieldDefinitionOrder(models.Model):
    """The "through" model for the :py:class:`FieldDefinition`_ <-> :py:class:`FormFieldSet`_ m2m
    relation. Defines the position of the field in the form set."""

    position = models.SmallIntegerField(
        blank=False, default=0, help_text="the position of the" "field in the row"
    )
    row = models.SmallIntegerField(
        blank=False,
        null=True,
        default=0,
        help_text="the row number of witch to render the" "field in. Null means it's own row each",
    )
    optional = models.BooleanField(
        default=False,
        help_text="If the field is required"
        "to be filled in by forms"
        "rendered with this "
        "attribute definition",
    )
    fieldset = models.ForeignKey(to=FormFieldSet, on_delete=models.CASCADE)
    definition = models.ForeignKey(to=FieldDefinition, on_delete=models.CASCADE)

    def __str__(self):
        return "{}(id: {}, def:{}, set:{}, optional:{}, row:{}, pos:{})".format(
            self.__class__.__name__,
            self.id,
            self.definition_id,
            self.fieldset_id,
            self.optional,
            self.row,
            self.position,
        )


class ValueMatch(TypeConversionValue):
    """
    Specifies an rule for an allowed attribute value.
    """

    definition = models.ForeignKey(
        to=FieldDefinition,
        on_delete=models.CASCADE,
        related_name="allowed_values",
    )

    display_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name used to render the field value (e.g. in a select box)",
    )

    def _test_value_type(self, value: Any) -> bool:
        """
        Check type, for float allow integers also
        unfortunately isinstance(True, int) == True, thus more code:

        :param value:
        :return:
        """
        type_ = self.VALUETYPE_FIELDNAME_LOOKUP[self.value_type][1]

        is_bool = isinstance(value, bool)
        if type_ == int:
            if is_bool:
                return False
            if not isinstance(value, int):
                return False
        elif type_ == float:
            if is_bool:
                return False
            if not isinstance(value, (float, int)):
                return False
        elif not isinstance(value, type_):
            return False
        return True

    def value_matches(self, value: Any) -> bool:
        """
        Checks type, value and range.

        The field `self.value_type` determines the `type` an value is allowed to have and decides
        which field (`self.value_bool`, `self.value_int`, `self.value_float`, `self.value_str`) it
        will use for the value match look up. If the corresponding field is `None` any value is
        allowed.

        Also checks if the value is within the bounds of `self.value_max` and `self.value_min` if
        applicable (for more see the fields descriptions).

        None values are rejected by default.
        """
        # reject None
        if value is None:
            return False

        # check if value is in range
        try:
            self._test_value_range(value)
        except ValueError:
            return False

        if not self._test_value_type(value):
            return False

        # check value
        if self.value is not None and value != self.value:
            return False

        return True


class Person(models.Model):
    """an actual registered persion"""

    uuid = models.CharField(max_length=40, unique=True)
    created = models.DateTimeField(db_index=True, default=django_now)
    updated = models.DateTimeField(db_index=True, default=django_now)

    @classmethod
    def save_from_dynamic_form(cls, dynamic_form: DynamicForm, django_form: Form, uuid: str):
        """create or update and person based on the given data

        FIXME: tests
        """
        uuid = uuid.upper()

        data = django_form.cleaned_data

        person, _ = cls.objects.get_or_create(uuid=uuid)
        with transaction.atomic():
            for field in dynamic_form.get_all_fields():
                value = data.get(field.name)
                if value is None or value == "":
                    continue

                # check attribute
                value = data[field.name]

                if field.is_multi_value_field() and hasattr(value, "__iter__"):
                    PersonalAttribute.objects.filter(person=person, name=field.name).delete()
                    for position, v in enumerate(value):
                        cls._validate_value(django_form, field, v)
                        cls._store_value(person, field, v, position)
                else:
                    cls._validate_value(django_form, field, value)
                    cls._store_value(person, field, value)

    @classmethod
    def _validate_value(cls, django_form: Form, field: FieldDefinition, value: Any):
        """ """
        if not field.is_allowed_value(value):
            # throw a form ValidationError
            err_msg = gettext_lazy(
                "Value {} is not allowed for {}".format(value, field.display_name_or_name())
            )
            django_form.add_error(field.name, err_msg)
            raise ValueError(err_msg)

    @classmethod
    def _store_value(cls, person: "Person", field: FieldDefinition, value: Any, position: int = 0):
        # store attribute
        attr, _ = PersonalAttribute.objects.get_or_create(
            person=person, name=field.name, position=position
        )
        match = field.get_value_match(value)
        attr.value_type = match.value_type
        attr.value = value

        value_name, _ = PersonalAttributeValueName.objects.get_or_create(
            name=match.display_name or field.display_name_or_name()
        )
        attr.value_name = value_name

        attr.updated = datetime.now(tz=settings.PYTZ_ZONE)
        attr.position = position
        attr.save()

    @classmethod
    def load_data_for_dynamic_form(cls, dynamic_form: DynamicForm, uuid: str) -> Mapping:
        """If the person exists, load the data matching the fields in the form

        FIXME: tests
        """
        try:
            person = cls.objects.get(uuid=uuid)
        except cls.DoesNotExist:
            return {}

        # get attributes shared between the person and the dynamic form
        matching_attributes = person.attributes.filter(
            name__in=dynamic_form.get_all_fields().values("name")
        )

        data = {}

        # multi-value fields are returned as list
        for attr in matching_attributes:
            if attr.name not in data:
                data[attr.name] = attr.value
            else:
                current_value = data[attr.name]
                if not isinstance(current_value, list):
                    current_value = [current_value]
                    data[attr.name] = current_value
                current_value.append(attr.value)

        return data

    def __str__(self):
        return "{}({}-{})".format(self.__class__.__name__, self.id, self.uuid)


class PersonalAttributeValueName(models.Model):
    """Store a name - value pair"""

    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Name used to render the field value (e.g. in a select box)",
    )

    def __str__(self):
        return "{}({}:{})".format(self.__class__.__name__, self.name, self.name)


class PersonalAttribute(TypeConversionValue):
    """An personal attribute like "age" or "gender"."""

    name = models.CharField(blank=False, max_length=100, db_index=True)
    value_name = models.ForeignKey(PersonalAttributeValueName, on_delete=models.CASCADE, null=True)
    created = models.DateTimeField(db_index=True, default=django_now)
    updated = models.DateTimeField(db_index=True, default=django_now)
    position = models.IntegerField(
        db_index=True, default=0, help_text="for multi-value fields," "the position within"
    )
    person = models.ForeignKey(to=Person, on_delete=models.CASCADE, related_name="attributes")

    class Meta:
        unique_together = ("name", "person", "position")

    def __str__(self):
        return "{}({}#{}:{} Person:{})".format(
            self.__class__.__name__, self.name, self.position, self.value, self.person_id
        )
