# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.test import TestCase

from primming.registration.models import FieldDefinition
from primming.registration.models import TypeConversionValue
from primming.registration.models import ValueMatch


class ModelAttributeValueMatchTestCase(TestCase):
    """tests for :py:class:`primming.registration.models.FieldDefinition`_"""

    def setUp(self) -> None:
        # type matchers - any value
        self.atTypeBool = FieldDefinition(name="NewsletterSignup")
        self.atTypeBool.save()

        ValueMatch(
            definition=self.atTypeBool, value_type=TypeConversionValue.ValueType.BOOLEAN
        ).save()

        # Range setup
        self.atTypeInt = FieldDefinition(name="Age")
        self.atTypeInt.save()

        ValueMatch(
            definition=self.atTypeInt,
            value_type=TypeConversionValue.ValueType.INTEGER,
            value_min=0,
            value_max=150,
        ).save()

        self.atTypeString = FieldDefinition(name="First Name")
        self.atTypeString.save()

        ValueMatch(
            definition=self.atTypeString,
            value_type=TypeConversionValue.ValueType.STRING,
            value_min=2,
            value_max=30,
        ).save()

        # Choice setup
        self.atChoice = FieldDefinition(name="Gender")
        self.atChoice.save()

        ValueMatch(
            definition=self.atChoice,
            value_type=TypeConversionValue.ValueType.STRING,
            value_string="Male",
        ).save()

        ValueMatch(
            definition=self.atChoice,
            value_type=TypeConversionValue.ValueType.STRING,
            value_string="Female",
        ).save()

        ValueMatch(
            definition=self.atChoice,
            value_type=TypeConversionValue.ValueType.STRING,
            value_string="Other",
        ).save()

    def test_bool(self):
        """test the setup for any boolean value"""
        self.assertTrue(self.atTypeBool.is_allowed_value(True))
        self.assertTrue(self.atTypeBool.is_allowed_value(False))
        self.assertFalse(self.atTypeBool.is_allowed_value(0))
        self.assertFalse(self.atTypeBool.is_allowed_value(1))
        self.assertFalse(self.atTypeBool.is_allowed_value(42))
        self.assertFalse(self.atTypeBool.is_allowed_value(2.718))
        self.assertFalse(self.atTypeBool.is_allowed_value(0.0))
        self.assertFalse(self.atTypeBool.is_allowed_value(1.1))
        self.assertFalse(self.atTypeBool.is_allowed_value("True"))
        self.assertFalse(self.atTypeBool.is_allowed_value("False"))
        self.assertFalse(self.atTypeBool.is_allowed_value(""))
        self.assertFalse(self.atTypeBool.is_allowed_value(None))

    def test_int_range(self):
        """test the integer range"""
        self.assertTrue(self.atTypeInt.is_allowed_value(42))
        self.assertTrue(self.atTypeInt.is_allowed_value(0))
        self.assertTrue(self.atTypeInt.is_allowed_value(150))
        self.assertFalse(self.atTypeInt.is_allowed_value(-1))
        self.assertFalse(self.atTypeInt.is_allowed_value(420))

    def test_string_range(self):
        """test the integer range"""
        self.assertTrue(self.atTypeString.is_allowed_value("Jo"))
        self.assertTrue(self.atTypeString.is_allowed_value("Joseph"))
        self.assertFalse(self.atTypeString.is_allowed_value("J"))
        self.assertFalse(self.atTypeString.is_allowed_value(""))
        self.assertFalse(self.atTypeString.is_allowed_value("01234567890123456789012345678901"))

    def test_choices(self):
        """test the choices"""

        self.assertEqual(3, len(list(self.atChoice.choices)))
        self.assertSetEqual({"Male", "Female", "Other"}, set(self.atChoice.choices))
        self.assertTrue(self.atChoice.is_allowed_value("Male"))
        self.assertTrue(self.atChoice.is_allowed_value("Female"))
        self.assertTrue(self.atChoice.is_allowed_value("Other"))
        self.assertFalse(self.atChoice.is_allowed_value("Hobbit"))
        self.assertFalse(self.atChoice.is_allowed_value(0))
        self.assertFalse(self.atChoice.is_allowed_value(2.718))
        self.assertFalse(self.atChoice.is_allowed_value(True))
        self.assertFalse(self.atChoice.is_allowed_value(False))
