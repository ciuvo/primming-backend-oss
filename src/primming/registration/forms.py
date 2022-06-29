# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from typing import Sequence

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from crispy_forms.layout import Fieldset
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms

from primming.registration.models import DynamicForm
from primming.registration.models import FieldDefinition
from primming.registration.models import FormFieldSet

BOOTSTRAP_FIELD_CLASS = ""
BOOTSTRAP_FIELD_WRAPPER_CLASS = "form-group p-2"
BOOTSTRAP_ROW_CLASS = "form-row flex-xl-row"
BOOTSTRAP_FIELDSET_CLASS = ""


class CrispyDynamicForm(forms.Form):
    """Create a crispy form from the :py:class:`primming.registration.models.DynamicForm`_ model."""

    def __init__(self, dynamic_form: DynamicForm, **kwargs):

        super().__init__(**kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "dynamic-form-{}".format(dynamic_form.id)
        self.helper.form_class = "PrimmingForm"
        self.helper.form_method = "post"

        if "form_action" in kwargs:
            self.helper.form_action = kwargs["form_action"]

        fieldsets = self._lay_out_fieldsets(self.get_sorted_fieldsets(dynamic_form))
        self.helper.layout = Layout(*fieldsets)
        self.helper.add_input(Submit("submit", "Submit"))

    def _lay_out_fieldsets(self, fieldsets) -> Sequence[Fieldset]:
        """crispy-layoutify the fieldsets"""
        result = []
        for fieldset in fieldsets:
            rows = self._lay_out_rows(self.get_rows(fieldset), fieldset)

            result.append(
                Fieldset(
                    fieldset.display_name_or_name(), *rows, css_class=BOOTSTRAP_FIELDSET_CLASS
                )
            )
        return result

    def _lay_out_rows(
        self, rows: Sequence[Sequence[FieldDefinition]], fieldset: FormFieldSet
    ) -> Sequence[Row]:
        """crispy-layoutify the rows"""
        result = []
        for row in rows:
            fields = self._lay_out_fields(row, fieldset)
            result.append(Row(*fields, css_class=BOOTSTRAP_ROW_CLASS))
        return result

    def _lay_out_fields(
        self, definitions: Sequence[FieldDefinition], fieldset: FormFieldSet
    ) -> Sequence[Field]:
        """crsipy-layoutify + add to self.fields for a list of FieldDefinitions"""
        fields = []
        for field in definitions:
            self.fields[field.name] = field.to_form_field(fieldset)
            fields.append(
                Field(
                    field.name,
                    css_class=BOOTSTRAP_FIELD_CLASS,
                    wrapper_class=BOOTSTRAP_FIELD_WRAPPER_CLASS,
                )
            )
        return fields

    @staticmethod
    def get_sorted_fieldsets(dynamic_form: DynamicForm) -> Sequence[FormFieldSet]:
        """get the fieldsets sorted by the position column"""
        return FormFieldSet.objects.filter(forms=dynamic_form.id).order_by(
            "fieldsetorder__position"
        )

    @staticmethod
    def get_rows(fieldset: FormFieldSet) -> Sequence[Sequence[FieldDefinition]]:
        """get the fielddefinitions grouped by row, ordered py position

        If two fields share the same 'row', they're grouped into one rows based
        on the value of the 'position'. Both fields belong to the intermediatary object.

        If the row is null, it will be grouped into it's own row.
        """
        fields = FieldDefinition.objects.filter(fieldsets=fieldset).order_by(
            "fielddefinitionorder__row",
            "fielddefinitionorder__position",
            "fielddefinitionorder__id",
        )

        row = []
        row_id = None
        for field in fields:
            fdo = field.fielddefinitionorder_set.get(fieldset=fieldset)
            if fdo.row is None:
                yield [field]
                continue

            # if the row id changes (or is None, yield the row)
            if fdo.row != row_id and row_id is not None:
                yield row
                row = []

            row.append(field)
            row_id = fdo.row
        yield row

    class Media:

        css = {"all": ("css/form.css",)}
        js = ("js/widgets/conditional.js",)
