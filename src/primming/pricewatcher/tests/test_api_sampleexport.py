from datetime import date
from datetime import datetime
from unittest import TestCase

import pytest
from django.conf import settings

from primming.pricewatcher.api import SampleExportApiMixin
from primming.pricewatcher.models import Browser
from primming.pricewatcher.models import City
from primming.pricewatcher.models import Country
from primming.pricewatcher.models import Device
from primming.pricewatcher.models import GeoIPLocation
from primming.pricewatcher.models import OperatingSystem
from primming.pricewatcher.models import Page
from primming.pricewatcher.models import PriceSample
from primming.pricewatcher.models import UserAgent
from primming.utils.api.exceptions import BadRequestException


class SampleExportApiMixinTestCase(TestCase):
    """
    tests for :py:class:`primming.pricewatcher.api.SampleExportApiMixin`_
    """

    @pytest.mark.django_db
    def setUp(self) -> None:
        self.testee = SampleExportApiMixin()

        page, _ = Page.objects.get_or_create(
            name="action0", url="https://action0.com", enabled=True
        )
        country, _ = Country.objects.get_or_create(iso_code="AT")
        city, _ = City.objects.get_or_create(country=country, geonameid="2763595")
        location, _ = GeoIPLocation.objects.get_or_create(
            ip="127.0.0.1", longitude=13.06, latitude=48.0, postal_code=4850, city=city
        )

        os, _ = OperatingSystem.objects.get_or_create(name="Linux", version="5.14")
        device, _ = Device.objects.get_or_create(name="Laptop", brand="Dell", version="9670")
        browser, _ = Browser.objects.get_or_create(name="Chrome", version="94")
        agent, _ = UserAgent.objects.get_or_create(os=os, device=device, browser=browser)

        self.sample = PriceSample(
            timestamp=datetime(2049, 7, 2, 14, tzinfo=settings.PYTZ_ZONE),
            price=100,
            currency="EUR",
            page=page,
            uuid="60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
            location=location,
            agent=agent,
        )

        super().setUp()

    @pytest.mark.django_db
    def test_validate_date_range_valid(self):
        """
        tests :py:class:`primming.pricewatcher.api.SampleExportApiMixin`_ with valid dates
        """
        _expected_start = date(2021, 7, 1)
        _expected_end = date(2022, 8, 23)

        start, end = self.testee._validate_date_range(
            _expected_start.strftime(self.testee.DATE_FORMAT),
            _expected_end.strftime(self.testee.DATE_FORMAT),
        )

        self.assertEqual(start, _expected_start)

        self.assertEqual(end, _expected_end)

    @pytest.mark.django_db
    def test_validate_date_range_order(self):
        """
        tests :py:class:`primming.pricewatcher.api.SampleExportApiMixin`_ with start after end
        """
        _expected_start = date(2023, 7, 1)
        _expected_end = date(2022, 8, 23)

        self.assertRaises(
            BadRequestException,
            self.testee._validate_date_range,
            _expected_start.strftime(self.testee.DATE_FORMAT),
            _expected_end.strftime(self.testee.DATE_FORMAT),
        )

    @pytest.mark.django_db
    def test_validate_date_range_format(self):
        """
        tests :py:class:`primming.pricewatcher.api.SampleExportApiMixin`_ with start after end
        """
        test_format = "%d-%Y-%m"
        _expected_start = date(2023, 7, 1)
        _expected_end = date(2022, 8, 23)

        self.assertNotEqual(self.testee.DATE_FORMAT, test_format)

        self.assertRaises(
            BadRequestException,
            self.testee._validate_date_range,
            _expected_start.strftime(test_format),
            _expected_end.strftime(test_format),
        )

    @pytest.mark.django_db
    def test_queryset(self):
        """
        tests :py:class:`primming.pricewatcher.api.SampleExportApiMixin._queryset`
        """
        page = self.sample.page

        samples = [
            PriceSample(
                timestamp=datetime(2021, 7, 1, tzinfo=settings.PYTZ_ZONE),
                price=100,
                currency="EUR",
                page=page,
                uuid="60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
            ),
            PriceSample(
                timestamp=datetime(2021, 7, 2, tzinfo=settings.PYTZ_ZONE),
                price=100,
                currency="EUR",
                page=page,
                uuid="60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
            ),
            PriceSample(
                timestamp=datetime(2021, 7, 2, 14, tzinfo=settings.PYTZ_ZONE),
                price=100,
                currency="EUR",
                page=page,
                uuid="60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
            ),
            PriceSample(
                timestamp=datetime(2021, 7, 3, 23, 59, 59, tzinfo=settings.PYTZ_ZONE),
                price=100,
                currency="EUR",
                page=page,
                uuid="60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
            ),
            PriceSample(
                timestamp=datetime(2021, 7, 4, tzinfo=settings.PYTZ_ZONE),
                price=100,
                currency="EUR",
                page=page,
                uuid="60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
            ),
        ]

        map(lambda s: s.save(), samples)
        ids = list(PriceSample.objects.order_by("id").values_list("id", flat=True))

        # test all
        self.assertListEqual(
            ids,
            sorted(
                self.testee._queryset(date(2021, 6, 30), date(2021, 7, 5)).values_list(
                    "id", flat=True
                )
            ),
        )

        # test middle set
        self.assertListEqual(
            ids[1:-1],
            sorted(
                self.testee._queryset(date(2021, 7, 2), date(2021, 7, 3)).values_list(
                    "id", flat=True
                )
            ),
        )

    @pytest.mark.django_db
    def test_serialize(self):
        """
        tests :py:class:`primming.pricewatcher.api.SampleExportApiMixin.serialize`
        """
        self.assertDictEqual(
            self.testee.serialize(self.sample),
            {
                "id": None,
                "timestamp": "2049-07-02T14:00:00+01:05",
                "url": "https://action0.com",
                "price": 100,
                "currency": "EUR",
                "uuid": "60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
                "browser": "Chrome",
                "browser_version": "94",
                "device": "Laptop",
                "device_brand": "Dell",
                "device_version": "9670",
                "os": "Linux",
                "postal_code": 4850,
                "geonames_city_id": "2763595",
                "country": "AT",
            },
        )

    @pytest.mark.django_db
    def test_samples(self):
        """
        tests :py:class:`primming.pricewatcher.api.SampleExportApiMixin.samples`
        """

        self.sample.save()
        self.assertDictEqual(
            list(self.testee.samples("2049-07-02", "2049-07-03"))[0],
            {
                "id": self.sample.id,
                "timestamp": "2049-07-02T12:55:00+00:00",
                "url": "https://action0.com",
                "price": 100,
                "currency": "EUR",
                "uuid": "60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE",
                "browser": "Chrome",
                "browser_version": "94",
                "device": "Laptop",
                "device_brand": "Dell",
                "device_version": "9670",
                "os": "Linux",
                "postal_code": "4850",
                "geonames_city_id": 2763595,
                "country": "AT",
            },
        )

    @pytest.mark.django_db
    def test_to_csv(self):
        """
        tests :py:class:`primming.pricewatcher.api.SampleExportApiMixin.to_csv`
        """
        result = list(self.testee.to_csv(iter([self.testee.serialize(self.sample)])))

        self.assertListEqual(
            result,
            [
                "id,timestamp,url,price,currency,uuid,browser,browser_version,device,device_brand,device_version,os,postal_code,geonames_city_id,country\r\n",
                ",2049-07-02T14:00:00+01:05,https://action0.com,100,EUR,60DD7B0D-4C03-4AD9-A61A-B2FD5D98F4FE,Chrome,94,Laptop,Dell,9670,Linux,4850,2763595,AT\r\n",
            ],
        )
