# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.http import Http404
from django.test import TestCase

from primming.pricewatcher.api import PageListViewApiMixin as plvam
from primming.pricewatcher.models import Page
from primming.pricewatcher.models import PageList
from primming.utils.api.exceptions import NotFoundException


class PageListViewMixinTestCase(TestCase):
    """tests for :class:`primming.pricewatcher.api.PagelistViewMixin`_"""

    def setUp(self) -> None:
        """ """
        self.page1 = Page(name="action0.com", url="https://action0.com")
        self.page2 = Page(name="action1.com", url="https://action1.com")
        self.page3 = Page(name="action2.com", url="https://action2.com")
        self.page4 = Page(name="action3.com", url="https://action3.com")
        self.page1.save()
        self.page2.save()
        self.page3.save()
        self.page4.save()
        self.pl1 = PageList(name="list1", default=False)
        self.pl2 = PageList(name="list2", default=True)
        self.pl1.save()
        self.pl2.save()
        self.pl1.pages.add(self.page1, self.page2)
        self.pl2.pages.add(self.page2, self.page3, self.page4)

    @staticmethod
    def _containsPage(data, page):
        for page_data in data["pages"]:
            if page_data["id"] == page.id and page_data["url"] == page.url:
                return True
        return False

    def test_serialize_list_404(self):
        """test :func:`primming.pricewatcher.api.PagelistViewMixin.serialize_list`_"""
        self.assertRaises(NotFoundException, plvam.serialize_list, "list3")

    def test_serialize_list_default(self):
        """test :func:`primming.pricewatcher.api.PagelistViewMixin.serialize_list`_"""
        ld_default = plvam.serialize_list()
        ld_2 = plvam.serialize_list("list2")
        self.assertEqual(ld_2, ld_default)
        self.assertTrue(self._containsPage(ld_2, self.page2))
        self.assertTrue(self._containsPage(ld_2, self.page3))
        self.assertTrue(self._containsPage(ld_2, self.page4))

    def test_serialize_list_named(self):
        """test :func:`primming.pricewatcher.api.PagelistViewMixin.serialize_list`_"""
        ld_1 = plvam.serialize_list("list1")
        self.assertEqual(len(ld_1["pages"]), 2)

        self.assertTrue(self._containsPage(ld_1, self.page1))
        self.assertTrue(self._containsPage(ld_1, self.page2))
