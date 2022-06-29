# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Sequence

from django.conf import settings
from django.db import models
from django.utils.timezone import now as django_now
from geoip2 import database as geodb
from user_agents import parse as uaparse

from primming.registration.models import Person


class Page(models.Model):
    """A single observed domain"""

    name = models.CharField(max_length=30, blank=False, unique=True)
    url = models.URLField(blank=False)
    enabled = models.BooleanField(default=True, blank=False)
    scraper = models.TextField(max_length=20_000)

    def __str__(self):
        return "{}(name:{}, enabled:{})".format(self.__class__.__name__, self.name, self.enabled)


class PageList(models.Model):
    """A list of observed domains"""

    name = models.CharField(max_length=30, blank=False, unique=True)
    default = models.BooleanField(default=False, null=True, blank=True, unique=True)
    pages = models.ManyToManyField(to=Page, related_name="lists")

    def save(self, *args, **kwargs):

        # make sure that there is only one default
        if self.default:
            if self.id:
                PageList.objects.exclude(id=self.id).update(default=False)
            else:
                PageList.objects.update(default=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return "{}(name:{}, default:{})".format(self.__class__.__name__, self.name, self.default)


class BrowserMake(models.Model):
    """Browser make

    TODO: replace name in the Browser model with a foreign key to BrowserMake"""

    name = models.CharField(max_length=50, blank=False, db_index=True)

    def __str__(self):
        return self.name


class Browser(models.Model):
    """the browser as determined by the user agent parser"""

    name = models.CharField(max_length=50, blank=False, db_index=True)
    version = models.CharField(max_length=20, blank=True, null=False, db_index=True)

    def __str__(self):
        return "{}(name:{}, version:{})".format(self.__class__.__name__, self.name, self.version)

    class Meta:
        unique_together = (("name", "version"),)


class Device(models.Model):
    """the device as determined by the user agent parser"""

    name = models.CharField(max_length=50, blank=False, db_index=True)
    brand = models.CharField(max_length=50, blank=False, db_index=True)
    version = models.CharField(max_length=20, blank=True, null=False, db_index=True)

    def __str__(self):
        return "{}(name:{}, version:{}, brand:{})".format(
            self.__class__.__name__, self.name, self.version, self.brand
        )

    class Meta:
        unique_together = (("name", "brand", "version"),)


class OperatingSystem(models.Model):
    """the os as determined by the user agent parser"""

    name = models.CharField(max_length=50, blank=False, db_index=True)
    version = models.CharField(max_length=20, blank=True, null=False, db_index=True)

    def __str__(self):
        return "{}(name:{}, version:{})".format(self.__class__.__name__, self.name, self.version)

    class Meta:
        unique_together = (("name", "version"),)


class UserAgent(models.Model):
    """the user agent as returned by the user agent parser"""

    browser = models.ForeignKey(to=Browser, on_delete=models.CASCADE)
    device = models.ForeignKey(to=Device, on_delete=models.CASCADE)
    os = models.ForeignKey(to=OperatingSystem, on_delete=models.CASCADE)

    @classmethod
    def from_ua_string(cls, ua_string: str) -> UserAgent:
        """
        Create or fetch the matching user agent based on the given string.
        :param ua_string: the user agent string as submitted by the http header
        :return: a user Agent object
        """
        ua = uaparse(ua_string)

        BrowserMake.objects.get_or_create(name=ua.browser.family)

        browser, _ = Browser.objects.get_or_create(
            name=ua.browser.family, version=ua.browser.version_string
        )

        device, _ = Device.objects.get_or_create(
            name=ua.device.family, brand=ua.device.brand or "", version=ua.browser.version_string
        )

        os, _ = OperatingSystem.objects.get_or_create(
            name=ua.os.family, version=ua.os.version_string
        )

        user_agent, _ = cls.objects.get_or_create(browser=browser, device=device, os=os)
        return user_agent

    def __str__(self):
        return "{}(browser:{}, device:{}, os:{})".format(
            self.__class__.__name__, self.browser, self.device, self.os
        )

    class Meta:
        unique_together = (("browser", "device", "os"),)


class Country(models.Model):
    """Country with 2-letter ISO Code"""

    iso_code = models.CharField(max_length=2, unique=True)

    def __str__(self):
        return self.iso_code


class City(models.Model):
    """City as returned by the geoip-ip database"""

    geonameid = models.IntegerField(db_index=True, unique=True)
    country = models.ForeignKey(to=Country, on_delete=models.CASCADE)

    @classmethod
    def from_geoip_location(
        cls,
        geoip_loc: Mapping[str, Any],
        locales: Sequence[str] = (
            "de",
            "en",
        ),
    ) -> City:
        """
        Get or create a :py:class:`City` object based on the city dictionary from the geoip
        database.

        :param geoip_loc: city dictionary from the geoip database.
        :param locales: list of locales we should try and store the name
        :return: an existing or newly created :py:class:`City` object
        """

        country, _ = Country.objects.get_or_create(iso_code=geoip_loc.country.iso_code)
        city, _ = City.objects.get_or_create(
            geonameid=geoip_loc.city.geoname_id,
            country=country,
        )

        for locale in locales:
            if locale in geoip_loc.city.names:
                CityName.objects.get_or_create(
                    name=geoip_loc.city.names[locale], city=city, locale=locale
                )

        return city

    def __str__(self):
        return "{}-{}".format(self.geonameid, self.country)


class CityName(models.Model):
    """The localized city name"""

    name = models.CharField(max_length=30, db_index=True)
    locale = models.CharField(max_length=6, db_index=True)
    city = models.ForeignKey(to=City, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("name", "locale", "city"),)

    def __str__(self):
        return "{}-{}".format(self.name, self.locale)


class GeoIPLocation(models.Model):
    """Model to store the location from the geo-ip database for an ip-address"""

    _reader = geodb.Reader(settings.IP_DATABASE)

    ip = models.CharField(max_length=15)
    longitude = models.DecimalField(decimal_places=6, max_digits=9)
    latitude = models.DecimalField(decimal_places=6, max_digits=9)
    postal_code = models.CharField(max_length=8, db_index=True)
    city = models.ForeignKey(to=City, on_delete=models.PROTECT)

    @classmethod
    def from_ipaddress(cls, ip_addr: str) -> GeoIPLocation:
        """create the location form the ip address

        :param ip_addr: the ip address
        :returns: a GeoIPLocation object
        :raises: geoip2.errors.AddressNotFoundError, KeyError, AttributeError"""
        entry = cls._reader.city(ip_addr)

        location, _ = GeoIPLocation.objects.get_or_create(
            ip=ip_addr,
            longitude=entry.location.longitude,
            latitude=entry.location.latitude,
            postal_code=entry.postal.code,
            city=City.from_geoip_location(entry),
        )

        return location

    class Meta:
        unique_together = (("ip", "longitude", "latitude", "postal_code", "city"),)

    def __str__(self):
        return "{ip}, {city}, {postal_code}".format(
            ip=self.ip, city=self.city, postal_code=self.postal_code
        )


class PriceSample(models.Model):
    """
    A price which has been extracted from an URL, by an person at a timestamp with a browser

    """

    timestamp = models.DateTimeField(db_index=True, default=django_now)
    price = models.IntegerField()
    currency = models.CharField(max_length=3)
    page = models.ForeignKey(to=Page, on_delete=models.CASCADE)

    uuid = models.CharField(max_length=40, db_index=True)
    agent = models.ForeignKey(to=UserAgent, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(
        to=GeoIPLocation, on_delete=models.SET_NULL, null=True, blank=True
    )

    @property
    def person(self):
        return Person.objects.filter(uuid=self.uuid).first()

    def __str__(self):
        return "{}(ts:{}, page:{}, price:{}, uuid:{}, agent:{}, location: {})".format(
            self.__class__.__name__,
            self.timestamp,
            self.page,
            self.price,
            self.uuid,
            self.agent,
            self.location,
        )


class BrowserRedirect(models.Model):
    """Redirects based on browser make. E.g. redirect firefox users to the install page for the
    extension on addons.mozilla.org and chrome users to the chrome webstore.
    """

    class RedirectPurpose(models.IntegerChoices):

        ADDON_WEBSTORE = 1, "Addon / Webstore"

    type = models.IntegerField(
        choices=RedirectPurpose.choices, default=RedirectPurpose.ADDON_WEBSTORE, null=False
    )

    url = models.URLField(max_length=2083)
    browser_make = models.ForeignKey(to=BrowserMake, on_delete=models.PROTECT, null=False)
    default = models.BooleanField(default=False)

    def __str__(self):
        return "{}(default={})".format(self.browser_make, self.default)
