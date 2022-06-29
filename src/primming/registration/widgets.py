# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.forms import NumberInput


class ConditionalMultiField(NumberInput):
    class Media:
        js = ("js/widgets/conditional_multifield.js",)

    template_name = "widgets/conditional_multi.html"

    def value_from_datadict(self, data, files, name):
        """we allow multiple"""
        return data.getlist(name)

    def format_value(self, values):
        """
        Return a value as it should appear when rendered in a template.
        """
        if hasattr(values, "__iter__"):
            return [NumberInput.format_value(self, value) for value in values]
        else:
            return [NumberInput.format_value(self, values)]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["values"] = context["widget"].pop("value")
        return context
