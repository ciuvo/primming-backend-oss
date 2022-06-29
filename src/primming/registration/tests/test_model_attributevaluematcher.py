# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.test import TestCase

from primming.registration.models import TypeConversionValue
from primming.registration.models import ValueMatch


class ModelAttributeValueMatchTestCase(TestCase):
    """tests for :py:class:`primming.registration.models.ValueMatch`_"""

    def setUp(self) -> None:
        # boolean matchers
        self.avmBoolAny = ValueMatch(value_type=TypeConversionValue.ValueType.BOOLEAN)
        self.avmBoolTrue = ValueMatch(
            value_type=TypeConversionValue.ValueType.BOOLEAN, value_bool=True
        )
        self.avmBoolFalse = ValueMatch(
            value_type=TypeConversionValue.ValueType.BOOLEAN, value_bool=False
        )

        # int matchers
        self.avmIntAny = ValueMatch(value_type=TypeConversionValue.ValueType.INTEGER)
        self.avmInt42 = ValueMatch(value_type=TypeConversionValue.ValueType.INTEGER, value_int=42)
        self.avmIntMin = ValueMatch(value_type=TypeConversionValue.ValueType.INTEGER, value_min=40)
        self.avmIntMax = ValueMatch(value_type=TypeConversionValue.ValueType.INTEGER, value_max=50)
        self.avmIntMinMax = ValueMatch(
            value_type=TypeConversionValue.ValueType.INTEGER, value_min=40, value_max=50
        )

        # float matchers
        self.avmFloatAny = ValueMatch(value_type=TypeConversionValue.ValueType.FLOAT)
        self.avmFloat2718 = ValueMatch(
            value_type=TypeConversionValue.ValueType.FLOAT, value_float=2.718
        )
        self.avmFloatMin = ValueMatch(
            value_type=TypeConversionValue.ValueType.FLOAT, value_min=3.1
        )
        self.avmFloatMax = ValueMatch(
            value_type=TypeConversionValue.ValueType.FLOAT, value_max=3.2
        )
        self.avmFloatMinMax = ValueMatch(
            value_type=TypeConversionValue.ValueType.FLOAT, value_min=3.1, value_max=3.2
        )

        # string matchers
        self.avmStringAny = ValueMatch(value_type=TypeConversionValue.ValueType.STRING)
        self.avmStringExact = ValueMatch(
            value_type=TypeConversionValue.ValueType.STRING,
            value_string="life, the universe and everything",
        )
        self.avmStringMin = ValueMatch(
            value_type=TypeConversionValue.ValueType.STRING,
            value_min=10,
        )
        self.avmStringMax = ValueMatch(
            value_type=TypeConversionValue.ValueType.STRING,
            value_max=34,
        )
        self.avmStringMinMax = ValueMatch(
            value_type=TypeConversionValue.ValueType.STRING,
            value_min=10,
            value_max=34,
        )

    def test_value_match_string(self):
        """test for `py:func:primming.registration.models.ValueMatch`"""
        self.assertTrue(self.avmStringAny.value_matches("test"))
        self.assertFalse(self.avmStringAny.value_matches(2.718))
        self.assertFalse(self.avmStringAny.value_matches(42))
        self.assertFalse(self.avmStringAny.value_matches(True))

        self.assertTrue(self.avmStringExact.value_matches("life, the universe and everything"))
        self.assertFalse(self.avmStringExact.value_matches("test"))
        self.assertFalse(self.avmStringExact.value_matches(42))
        self.assertFalse(self.avmStringExact.value_matches(2.718))
        self.assertFalse(self.avmStringExact.value_matches(True))

        self.assertTrue(self.avmStringMin.value_matches("life, the universe and everything"))
        self.assertFalse(self.avmStringMin.value_matches("test"))

        self.assertTrue(self.avmStringMax.value_matches("life, the universe and everything"))
        self.assertFalse(self.avmStringMax.value_matches("0123456789012345678901234567890123456"))

        self.assertTrue(self.avmStringMinMax.value_matches("life, the universe and everything"))
        self.assertFalse(self.avmStringMinMax.value_matches("test"))
        self.assertFalse(
            self.avmStringMinMax.value_matches("0123456789012345678901234567890123456")
        )

    def test_value_match_float(self):
        """test for `py:func:primming.registration.models.ValueMatch`"""
        self.assertTrue(self.avmFloatAny.value_matches(0.0))
        self.assertTrue(self.avmFloatAny.value_matches(2.718))
        self.assertTrue(self.avmFloatAny.value_matches(42))
        self.assertFalse(self.avmFloatAny.value_matches(True))
        self.assertFalse(self.avmFloatAny.value_matches("test"))

        self.assertTrue(self.avmFloat2718.value_matches(2.718))
        self.assertFalse(self.avmFloat2718.value_matches(3.14))

        self.assertTrue(self.avmFloatMin.value_matches(3.14))
        self.assertFalse(self.avmFloatMin.value_matches(3.05))

        self.assertTrue(self.avmFloatMax.value_matches(3.14))
        self.assertFalse(self.avmFloatMax.value_matches(3.25))

        self.assertTrue(self.avmFloatMinMax.value_matches(3.14))
        self.assertFalse(self.avmFloatMinMax.value_matches(3.05))
        self.assertFalse(self.avmFloatMinMax.value_matches(3.25))

    def test_value_match_int(self):
        """test for `py:func:primming.registration.models.ValueMatch`"""
        self.assertTrue(self.avmIntAny.value_matches(0))
        self.assertTrue(self.avmIntAny.value_matches(42))
        self.assertFalse(self.avmIntAny.value_matches(2.718))
        self.assertFalse(self.avmIntAny.value_matches(False))
        self.assertFalse(self.avmIntAny.value_matches("test"))

        self.assertTrue(self.avmInt42.value_matches(42))
        self.assertFalse(self.avmInt42.value_matches(41))
        self.assertFalse(self.avmInt42.value_matches(-1))

        self.assertTrue(self.avmIntMin.value_matches(42))
        self.assertFalse(self.avmIntMin.value_matches(39))

        self.assertTrue(self.avmIntMax.value_matches(42))
        self.assertFalse(self.avmIntMax.value_matches(51))

        self.assertTrue(self.avmIntMinMax.value_matches(42))
        self.assertFalse(self.avmIntMinMax.value_matches(51))
        self.assertFalse(self.avmIntMinMax.value_matches(39))
        self.assertFalse(self.avmIntMinMax.value_matches(-1))

    def test_value_match_bool(self):
        """test for `py:func:primming.registration.models.ValueMatch`"""
        self.assertTrue(self.avmBoolAny.value_matches(True))
        self.assertTrue(self.avmBoolAny.value_matches(False))
        self.assertFalse(self.avmBoolAny.value_matches("test"))
        self.assertFalse(self.avmBoolAny.value_matches(42))
        self.assertFalse(self.avmBoolAny.value_matches(2.718))

        self.assertTrue(self.avmBoolTrue.value_matches(True))
        self.assertFalse(self.avmBoolTrue.value_matches(False))
        self.assertFalse(self.avmBoolTrue.value_matches("test"))
        self.assertFalse(self.avmBoolTrue.value_matches(42))
        self.assertFalse(self.avmBoolTrue.value_matches(2.718))

        self.assertTrue(self.avmBoolFalse.value_matches(False))
        self.assertFalse(self.avmBoolFalse.value_matches(True))
        self.assertFalse(self.avmBoolFalse.value_matches("test"))
        self.assertFalse(self.avmBoolFalse.value_matches(42))
        self.assertFalse(self.avmBoolFalse.value_matches(2.718))
