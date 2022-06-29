# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from primming.admin import admin_site
# Register your models here.
from primming.pricewatcher.models import BrowserRedirect
from primming.pricewatcher.models import Page
from primming.pricewatcher.models import PageList
from primming.pricewatcher.models import PriceSample
from primming.pricewatcher.models import UserAgent


class ReadOnlyAdminMixin(object):
    """Disables all editing capabilities.

    https://djangosnippets.org/snippets/10539/"""

    change_form_template = "admin/view.html"

    def __init__(self, *args, **kwargs):
        super(ReadOnlyAdminMixin, self).__init__(*args, **kwargs)
        self.readonly_fields = [f.name for f in self.model._meta.get_fields()]

    def get_actions(self, request):
        actions = super(ReadOnlyAdminMixin, self).get_actions(request)
        del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


def linkify(field_name):
    """
    https://stackoverflow.com/questions/37539132/display-foreign-key-columns-as-link-to-detail-object-in-django-admin/53092940#53092940  # NOQA
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """

    def _linkify(obj):
        linked_obj = getattr(obj, field_name)
        if linked_obj is None:
            return "-"
        app_label = linked_obj._meta.app_label
        model_name = linked_obj._meta.model_name
        view_name = f"admin:{app_label}_{model_name}_change"
        link_url = reverse(view_name, args=[linked_obj.pk])
        return format_html('<a href="{}">{}</a>', link_url, linked_obj)

    _linkify.short_description = field_name  # Sets column name
    return _linkify


class PageInline(admin.TabularInline):
    model = Page.lists.through
    extra = 0


class PageListAdmin(admin.ModelAdmin):
    inlines = [PageInline]
    list_display = ("name", "page_count", "default")
    fields = ("name", "default")

    def page_count(self, obj):
        return obj.pages.count()


admin_site.register(PageList, PageListAdmin)


class PageAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "enabled")


admin_site.register(Page, PageAdmin)


class UserAgentAdmin(admin.ModelAdmin, ReadOnlyAdminMixin):
    list_display = ("browser", "device", "os")


admin_site.register(UserAgent, UserAgentAdmin)


class PriceSampleAdmin(admin.ModelAdmin, ReadOnlyAdminMixin):

    list_display = (
        "timestamp",
        linkify("page"),
        "fprice",
        "uuid",
        linkify("person"),
        linkify("agent"),
    )
    readonly_fields = ()

    def fprice(self, obj):
        return "{} {}".format(obj.price / 100.0, obj.currency)


admin_site.register(PriceSample, PriceSampleAdmin)


class BrowserRedirectAdmin(admin.ModelAdmin):

    list_display = ("type", "browser_make", "default", "url")
    list_filter = ("type", "browser_make", "default")


admin_site.register(BrowserRedirect, BrowserRedirectAdmin)
