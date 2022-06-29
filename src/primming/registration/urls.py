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
from primming.registration.views import RegistrationFormView
from primming.registration.views import RegistrationSuccessView

# example uuid: 41cb55b0-56c0-4b1f-bde3-ffb90148d520
urlpatterns = [
    re_path(r"(?P<form_name>\w*)/(?P<uuid>" + UUID_PATTERN + ")", RegistrationFormView.as_view()),
    re_path(r"(?P<uuid>" + UUID_PATTERN + ")", RegistrationFormView.as_view()),
    path("success", RegistrationSuccessView.as_view(), name="registration_success"),
]
