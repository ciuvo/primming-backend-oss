# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy


class PrimmingAdminSite(AdminSite):
    site_title = gettext_lazy("Primming Admin")
    site_header = gettext_lazy("Primming Admin")
    index_title = gettext_lazy("Primming Admin")


admin_site = PrimmingAdminSite(name="primmingAdmin")
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
