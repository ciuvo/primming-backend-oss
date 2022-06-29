# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.test import TestCase

from primming.registration.forms import CrispyDynamicForm
from primming.registration.models import DynamicForm


class DynamicFormTestCase(TestCase):
    """tests for :py:func:`CrispyDynamicForm`"""

    fixtures = ["test_dynamicform.yaml"]

    def test_get_sorted_fieldsets(self):
        """tests for :py:func:`CrispyDynamicForm.get_sorted_Fieldsets`_"""

        form = DynamicForm.objects.get(id=1)
        fieldsets = CrispyDynamicForm.get_sorted_fieldsets(form)

        def test_ascending_order(fss):
            last_pos = None
            for fs in fss:
                pos = fs.fieldsetorder_set.get(form=form).position
                if last_pos is None:
                    last_pos == fs.fieldsetorder_set.get(form=form).position
                else:
                    self.assertGreaterEqual(last_pos, pos)

        def reverse_order(fss):
            for idx, fs in enumerate(reversed(fss)):
                fso = fs.fieldsetorder_set.get(form=form, fieldset=fs)
                fso.position = idx
                fso.save()

        # reverse, fetch again, test again
        reverse_order(fieldsets)
        fieldsets = CrispyDynamicForm.get_sorted_fieldsets(form)
        test_ascending_order(fieldsets)

    def test_get_rows(self):
        """tests for :py:func:`CrispyDynamicForm.get_rows`_"""
        form = DynamicForm.objects.get(id=1)
        fieldset = CrispyDynamicForm.get_sorted_fieldsets(form)[1]
        rows = list(CrispyDynamicForm.get_rows(fieldset))

        # check the fixture for the configured orders

        # check the fields with row = NULL
        self.assertEqual(1, len(rows[0]))
        self.assertEqual("Row-Null-1", rows[0][0].name)
        self.assertEqual(1, len(rows[1]))
        self.assertEqual("Row-Null-2", rows[1][0].name)

        # [<FieldDefinition: FieldDefinition(5:Age:None)>,
        #  <FieldDefinition: FieldDefinition(6:Gender:None)>]
        self.assertEqual(2, len(rows[2]))
        self.assertEqual("Age", rows[2][0].name)
        self.assertEqual("Gender", rows[2][1].name)

        # [<FieldDefinition: FieldDefinition(7:Browser:None)>,
        #  <FieldDefinition: FieldDefinition(8:Device:None)>]
        self.assertEqual(2, len(rows[3]))
        self.assertEqual("Browser", rows[3][0].name)
        self.assertEqual("Device", rows[3][1].name)
