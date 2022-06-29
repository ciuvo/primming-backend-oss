# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
"""primming URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.urls import re_path

from primming.constants import UUID_PATTERN
from primming.pricewatcher.views import ExportPersonsApiView
from primming.pricewatcher.views import ExportSamplesApiView
from primming.pricewatcher.views import IsRegisteredView
from primming.pricewatcher.views import PageListView
from primming.pricewatcher.views import RedirectToWebstore
from primming.pricewatcher.views import ScraperView
from primming.pricewatcher.views import SubmitPriceReport

urlpatterns = [
    re_path(
        r"api/1.0/urllist/(?P<list_name>\w*)/(?P<uuid>" + UUID_PATTERN + ")?",
        PageListView.as_view(),
    ),
    re_path(r"api/1.0/urllist/(?P<uuid>" + UUID_PATTERN + ")?", PageListView.as_view()),
    re_path(r"api/1.0/prices/(?P<uuid>" + UUID_PATTERN + ")?", SubmitPriceReport.as_view()),
    re_path(r"api/1.0/surveyed/(?P<uuid>" + UUID_PATTERN + ")?", IsRegisteredView.as_view()),
    path(r"api/1.0/scraper/analyze", ScraperView.as_view()),
    re_path(
        r"api/1.0/export/samples/(?P<start>\d{4}-\d{2}-\d{2})/(?P<end>\d{4}-\d{2}-\d{2})/?",
        ExportSamplesApiView.as_view(),
    ),
    re_path(
        r"api/1.0/export/persons/(?P<start>\d{4}-\d{2}-\d{2})/(?P<end>\d{4}-\d{2}-\d{2})/?",
        ExportPersonsApiView.as_view(),
    ),
    path("webstore", RedirectToWebstore.as_view()),
]
