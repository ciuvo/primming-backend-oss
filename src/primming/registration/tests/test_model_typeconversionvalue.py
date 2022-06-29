# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.test import TestCase

from primming.registration.models import PersonalAttribute as TypeConversionValue


class ModelTypeConversionValueTestCase(TestCase):
    """tests for :py:class:`primming.registration.models.TypeConversionValue`_

    Note: we do not do type check since we expect django to take care of these
    """

    def test_assign_bool(self):
        """test bool assignment."""
        m = TypeConversionValue()
        m.value_type = TypeConversionValue.ValueType.BOOLEAN

        # unset it is None
        self.assertIsNone(m.value_bool)

        m.value = True
        self.assertTrue(m.value)

        m.value = False
        self.assertFalse(m.value)

    def test_assign_int(self):
        """test int assignment"""
        m = TypeConversionValue()
        m.value_type = TypeConversionValue.ValueType.INTEGER

        # unset it is None
        self.assertIsNone(m.value_int)

        m.value = 42
        self.assertEqual(m.value, 42)

        # test range violations
        m.value_max = 50
        m.value_min = 10

        def assign(v):
            m.value = v

        # test out of range values
        self.assertRaises(ValueError, assign, 0)
        self.assertRaises(ValueError, assign, 1)
        self.assertRaises(ValueError, assign, -1)
        self.assertRaises(ValueError, assign, 68)
        self.assertRaises(ValueError, assign, 419)

        # test in range value
        m.value = 21
        self.assertEqual(m.value, 21)

    def test_assign_float(self):
        """test float assignment"""
        m = TypeConversionValue()
        m.value_type = TypeConversionValue.ValueType.FLOAT

        # unset it is None
        self.assertIsNone(m.value_float)

        m.value = 42.21
        self.assertEqual(m.value, 42.21)

        # test range violations
        m.value_max = 51.3
        m.value_min = 20.5

        def assign(v):
            m.value = v

        # test out of range values
        self.assertRaises(ValueError, assign, 0)
        self.assertRaises(ValueError, assign, 20.4)
        self.assertRaises(ValueError, assign, 51.4)
        self.assertRaises(ValueError, assign, 60)

        # test in range value
        m.value = 21.42
        self.assertEqual(m.value, 21.42)

    def test_assign_string(self):
        """test float assignment"""
        m = TypeConversionValue()
        m.value_type = TypeConversionValue.ValueType.STRING

        # unset it is None
        self.assertIsNone(m.value_string)

        m.value = "the answer is 42"
        self.assertEqual(m.value, "the answer is 42")

        # test range violations
        m.value_max = 30
        m.value_min = 10

        def assign(v):
            m.value = v

        # test out of range values
        self.assertRaises(ValueError, assign, "")
        self.assertRaises(ValueError, assign, "test")
        self.assertRaises(
            ValueError, assign, "what is the meaning of life, the universe and the rest?"
        )

        # test in range value (I do write jokes in base 13)
        m.value = "what is 6 times 9"
        self.assertEqual(m.value, "what is 6 times 9")
