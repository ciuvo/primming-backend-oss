# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import json

from django.test import TestCase

from primming.pricewatcher.api import BadRequestException
from primming.pricewatcher.api import SubmitPriceReportApiMixin


class SubmitPriceReportApiMixinTestCase(TestCase):
    """tests for :class:`primming.pricewatcher.api.SubmitPriceReportApiMixin"""

    def test_validate_str(self):
        """tests for :func:`primming.pricewatcher.api.SubmitPriceReportApiMixin.validate_str"""

        self.assertRaises(BadRequestException, SubmitPriceReportApiMixin.validate_str, None)
        self.assertRaises(BadRequestException, SubmitPriceReportApiMixin.validate_str, {})
        self.assertRaises(BadRequestException, SubmitPriceReportApiMixin.validate_str, False)
        self.assertEqual(SubmitPriceReportApiMixin.validate_str("x" * 10, max_length=3), "xxx")
        self.assertEqual(SubmitPriceReportApiMixin.validate_str("xxx", max_length=10), "xxx")

    def test_validate_price(self):
        """tests for :func:`primming.pricewatcher.api.SubmitPriceReportApiMixin.validate_price"""

        self.assertRaises(BadRequestException, SubmitPriceReportApiMixin.validate_price, "")
        self.assertRaises(BadRequestException, SubmitPriceReportApiMixin.validate_price, False)
        self.assertRaises(BadRequestException, SubmitPriceReportApiMixin.validate_price, [])
        self.assertDictEqual(SubmitPriceReportApiMixin.validate_price({}), {})
        self.assertDictEqual(
            SubmitPriceReportApiMixin.validate_price({"value": 234567}), {"value": "234567"}
        )
        self.assertDictEqual(
            SubmitPriceReportApiMixin.validate_price({"currency": ""}), {"currency": ""}
        )
        self.assertDictEqual(
            SubmitPriceReportApiMixin.validate_price({"currency": "EUR"}), {"currency": "EUR"}
        )
        self.assertDictEqual(
            SubmitPriceReportApiMixin.validate_price(
                {"value": "123", "currency": "EUR", "extra": "xx"}
            ),
            {"value": "123", "currency": "EUR"},
        )

    def test_validate_body(self):
        """tests for :func:`primming.pricewatcher.api.SubmitPriceReportApiMixin.validate_body"""

        # validate_body returns a generator, call list on it
        self.assertRaises(BadRequestException, list, SubmitPriceReportApiMixin.validate_body(""))
        self.assertRaises(
            BadRequestException, list, SubmitPriceReportApiMixin.validate_body("xxx")
        )
        self.assertRaises(BadRequestException, list, SubmitPriceReportApiMixin.validate_body({}))
        self.assertDictEqual(
            next(
                SubmitPriceReportApiMixin.validate_body(
                    json.dumps(
                        [
                            {
                                "url": "https://action0.com",
                                "price": {"value": "123", "currency": "EUR", "extra": "x"},
                            }
                        ]
                    ).encode("utf-8")
                )
            ),
            {
                "url": "https://action0.com",
                "price": {"value": "123", "currency": "EUR"},
            },
        )
