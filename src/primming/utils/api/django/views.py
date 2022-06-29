# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import asyncio

from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.utils.decorators import classonlymethod
from django.views.generic import View

from primming.utils.api.exceptions import BadRequestException
from primming.utils.api.exceptions import NotFoundException


class SyncView(View):
    """A view that allows to raise exceptions for 40x responses"""

    def dispatch(self, request, *args, **kwargs):
        """allow to return 4xx responses via exceptions"""
        try:
            return super().dispatch(request, *args, **kwargs)
        except BadRequestException as e:
            return HttpResponseBadRequest(str(e))
        except NotFoundException as e:
            return HttpResponseNotFound(str(e))


class AsyncView(SyncView):
    """view with async support"""

    @classonlymethod
    def as_view(cls, **kwargs):
        """
        https://stackoverflow.com/questions/62038200/correct-way-to-use-async-class-based-views-in-django  #NOQA
        """
        view = super().as_view(**kwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine  # NOQA
        return view
