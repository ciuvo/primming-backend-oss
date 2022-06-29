# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import logging

from asgiref.sync import sync_to_async
from basicauth.decorators import basic_auth_required
from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from user_agents import parse as uaparse

from primming.pricewatcher.api import PageListViewApiMixin
from primming.pricewatcher.api import PersonsExportApiMixin
from primming.pricewatcher.api import SampleExportApiMixin
from primming.pricewatcher.api import SubmitPriceReportApiMixin
from primming.pricewatcher.api import UserRegistrationAPIMixin
from primming.pricewatcher.models import BrowserRedirect
from primming.pricewatcher.models import Page
from primming.utils.api.django.views import AsyncView
from primming.utils.api.django.views import SyncView
from primming.utils.api.exceptions import BadRequestException
from primming.utils.api.exceptions import NotFoundException

log = logging.getLogger(__name__)


class PageListView(PageListViewApiMixin, AsyncView):
    """
    Endpoint for the extension to fetch the list of URLs to observe
    """

    async def get(
        self, request: HttpRequest, list_name: str = None, uuid: str = None, **kwargs
    ) -> JsonResponse:
        """ """
        log.debug("Sending list of pages (%s:%s)", uuid, list_name)
        data = await sync_to_async(self.serialize_list)(name=list_name)
        return JsonResponse(data)


@method_decorator(csrf_exempt, name="dispatch")
class SubmitPriceReport(SubmitPriceReportApiMixin, AsyncView):
    """Endpoint for the price sampling submission"""

    async def post(
        self, request: HttpRequest, list_name: str = None, uuid: str = None
    ) -> JsonResponse:
        """receive the info from the extension and put it in the celery queue"""
        log.info("Got prices from (%s:%s)", uuid, list_name)

        body = list(self.validate_body(request.body))
        uuid = uuid.upper()

        await sync_to_async(self.delay_pricelogger)(
            uuid,
            body,
            request.META["HTTP_USER_AGENT"],
            request.META["HTTP_X_FORWARDED_FOR"],
        )
        return JsonResponse({"result": "ok"})


class IsRegisteredView(UserRegistrationAPIMixin, AsyncView):
    """
    API view to indicate whether the uuid has finished the registration
    """

    async def get(self, request: HttpRequest, uuid: str) -> JsonResponse:
        """Handle GET requests: instantiate a blank version of the form."""
        is_registered = await sync_to_async(self.is_registered)(uuid=uuid)
        return JsonResponse({"completed": is_registered})


class ExportAPIViewBase(SyncView):
    """ """

    filename_base = "export"

    def get(self, request: HttpRequest, start: str, end: str) -> HttpResponse:
        """Handle GET requests"""
        samples = self.samples(start, end)
        accept = request.META.get("HTTP_ACCEPT")
        mime_type, data = self.negotiate(samples, accept)
        response = HttpResponse(data, content_type=mime_type)
        response.streaming = True
        response["Content-Disposition"] = "attachment; filename=%s_%s-%s.%s" % (
            self.filename_base,
            start,
            end,
            mime_type.split("/")[-1],
        )
        return response


@method_decorator(basic_auth_required, name="dispatch")
class ExportSamplesApiView(SampleExportApiMixin, ExportAPIViewBase):

    filename_base = "samples"


@method_decorator(basic_auth_required, name="dispatch")
class ExportPersonsApiView(PersonsExportApiMixin, ExportAPIViewBase):

    filename_base = "persons"


class RedirectToWebstore(AsyncView):
    """Redirect the user to the extension store based on their browser make."""

    def redirect_for_browser(self, user_agent: str):
        """ """
        ua = uaparse(user_agent)
        browser_make = ua.browser.family

        # get redirect for the browser make
        redirect = BrowserRedirect.objects.filter(
            browser_make__name=browser_make,
            type=BrowserRedirect.RedirectPurpose.ADDON_WEBSTORE,
        ).first()

        # get the default fallback
        if not redirect:
            redirect = BrowserRedirect.objects.get(
                type=BrowserRedirect.RedirectPurpose.ADDON_WEBSTORE, default=True
            )

        return redirect.url

    async def get(self, request: HttpRequest):

        url = await sync_to_async(self.redirect_for_browser)(request.META["HTTP_USER_AGENT"])
        return HttpResponseRedirect(url)


class ScraperView(AsyncView):
    """Emulate the ciuvo API's scraper endpoint in order to allow supporting the browser extension
    without the ciuvo API at the cost of maintaining the scrapers here.
    """

    def response_for_url(self, url: str) -> HttpResponse:
        """
        Produce the scraper response for the given URL

        TODO: caching
        """
        page = Page.objects.filter(url=url.strip()).first()
        if not page:
            log.info("Could not find page with url: %s", url)
            raise NotFoundException("No scraper found for '%s'" % url)

        response = JsonResponse({"csl": page.scraper})
        response["Cache-Control"] = "max-age=%d" % settings.CACHE_CONTROL_SCRAPER_TIMEOUT
        return response

    async def get(self, request: HttpRequest) -> HttpResponse:

        url = request.GET.get("url")
        if not url:
            raise BadRequestException("Parameter 'url' is missing.")

        return await sync_to_async(self.response_for_url)(url)
