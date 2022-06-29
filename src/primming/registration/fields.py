# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.forms import IntegerField


class ConditionalMultiValueField(IntegerField):
    def clean(self, values):
        return [super(ConditionalMultiValueField, self).clean(v) for v in values]
