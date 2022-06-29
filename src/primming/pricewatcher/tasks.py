# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import logging
from datetime import datetime
from typing import Mapping
from typing import Sequence

import geoip2.errors
from django.conf import settings

from ecciuvo.price import clean_price
from primming.pricewatcher.models import GeoIPLocation
from primming.pricewatcher.models import Page
from primming.pricewatcher.models import PriceSample
from primming.pricewatcher.models import UserAgent
from primming.utils.celery import AutoRegisterTask

log = logging.getLogger(__name__)


class PriceLoggerTask(AutoRegisterTask):
    """store the price samples submitted by the user"""

    def _price_ok(self, price, scraped_page):
        """check if the price makes sense"""
        if not price or not isinstance(price, dict):
            log.warning("Price is missing for: %s", scraped_page)
            price_value = None
        else:
            price_value = price.get("value")

        if not price_value:
            log.warning("Price on %s could not be parsed: %s", scraped_page["url"], price)
            return False
        return True

    def run(self, uuid: str, data: Sequence[Mapping], user_agent: str, remote_ip: str):
        """log the price sample as submitted by the extension"""
        user_agent = UserAgent.from_ua_string(user_agent)
        timestamp = datetime.now(tz=settings.PYTZ_ZONE)

        try:
            location = GeoIPLocation.from_ipaddress(remote_ip)
        except (geoip2.errors.GeoIP2Error, KeyError, AttributeError):
            location = None

        for scraped_page in data:
            try:
                page = Page.objects.get(url=scraped_page["url"])

                price = scraped_page.get("price")
                if not self._price_ok(price, scraped_page):
                    continue

                price, currency = clean_price(price.get("value"), price.get("curr"))
                sample = PriceSample(
                    timestamp=timestamp,
                    uuid=uuid,
                    agent=user_agent,
                    page=page,
                    currency=currency,
                    price=price,
                    location=location,
                )
                sample.save()
                log.info("Added sample: %s", sample)
            except Page.DoesNotExist as e:
                log.error("Got event for unknown page: ", e)
