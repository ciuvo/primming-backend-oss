import csv
import json
import logging
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Generator
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple

from django.conf import settings
from django.db.models import QuerySet

from primming.pricewatcher.models import PageList
from primming.pricewatcher.models import PriceSample
from primming.pricewatcher.tasks import PriceLoggerTask
from primming.registration.models import Person
from primming.registration.models import PersonalAttribute
from primming.utils.api.exceptions import BadRequestException
from primming.utils.api.exceptions import NotFoundException


class StreamingEchoBuffer:
    """Django's StreamingHttpResponse requires a generator which produces byte lines.

    The writerow() method returns the returned value from the write method of the underlying file
    buffer. This is an underlying buffer which just returns what is was given.

    Inspired by: https://code.djangoproject.com/ticket/21179#comment:10"""

    def write(self, value):
        return value


class PageListViewApiMixin:
    """Mixin for the list of observed pages endpoint"""

    @staticmethod
    def serialize_list(name: str = None) -> Mapping:
        """TODO: document + tests"""
        if name is None:
            lst = PageList.objects.filter(default=True).first()
        else:
            lst = PageList.objects.filter(name=name).first()

        if not lst:
            raise NotFoundException

        return {
            "version": settings.VERSION,
            "list": lst.id,
            "pages": [{"id": p.id, "url": p.url} for p in lst.pages.all()],
        }


class SubmitPriceReportApiMixin:
    """Mixin for the price report api endpoint"""

    @classmethod
    def validate_price(cls, price: Mapping):
        """validate the price object as submitted"""
        if price is None:
            return None

        if not isinstance(price, dict):
            raise BadRequestException("Cannot validate price.")

        clean_price = {}

        if "value" in price and price["value"] is not None:
            value = price["value"]
            if isinstance(value, (int, float)):
                value = str(value)
            clean_price["value"] = cls.validate_str(value)

        if "currency" in price and price["currency"] is not None:
            clean_price["currency"] = cls.validate_str(price["currency"])

        return clean_price

    @classmethod
    def validate_str(cls, string_: str, max_length: int = 2083) -> str:
        """validate the url of a submitted document

        :param string_: the string to validate
        :param max_length: the maxium length to truncate the string to, default 2083 (IE URL limit)
        """
        if isinstance(string_, str):
            return string_[0:max_length]
        else:
            raise BadRequestException("Cannot validate request")

    @classmethod
    def validate_body(cls, body: bytes) -> Iterable:
        """validate the submitted body.

        TODO: needs to be revisited?
         - maybe use a django form for validation?
         - maybe use fastjsonschema?
        """
        try:
            body = body.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            raise BadRequestException("Cannot decode request body")

        try:
            body = json.loads(body)
        except UnicodeDecodeError:
            raise BadRequestException("Cannot decode json")

        if not isinstance(body, list):
            raise BadRequestException("Badly formed document")

        for d in body:
            try:
                yield {
                    "url": cls.validate_str(d["url"]),
                    "price": cls.validate_price(d.get("price")),
                }
            except BaseException as e:
                logging.exception("Cannot validate sample: %s (%s)", d, e)

    def delay_pricelogger(
        self, uuid: str, body: Sequence[Mapping], user_agent: str, remote_ip: str
    ):
        """hand the info over to the celery task

        :param uuid: the uuid
        :param body: the extracted prices, url <-> price tuples
        :param user_agent: the user agent to determine the browser/device/os
        :param remote_ip: the ip to determine the location

        """
        PriceLoggerTask().delay(uuid, body, user_agent, remote_ip)


class UserRegistrationAPIMixin:
    @staticmethod
    def is_registered(uuid: str) -> bool:
        """

        :param uuid:
        :return:
        """

        try:
            Person.objects.get(uuid=uuid)
            return True
        except Person.DoesNotExist:
            return False


class SimpleRestAPISupport:
    """Export :py:class:`primming.pricewatcher.models.PriceSample` in a streaming fashion

    TODO: Initially I found django-rest-api too heavy for this simple export, but now it seemed
    like the better idea..
    """

    DATE_FORMAT = "%Y-%m-%d"
    MIME_TYPES_JSON = ("application/json",)
    MIME_TYPES_CSV = ("text/csv",)

    model = None
    prefetch_related = []
    date_column = "timestamp"

    def _validate_date_range(self, start_date: str, end_date: str) -> Tuple[datetime, date]:
        """validate the submitted date ranges"""
        try:
            start = datetime.strptime(start_date, self.DATE_FORMAT).date()
            end = datetime.strptime(end_date, self.DATE_FORMAT).date()
        except ValueError as e:
            raise BadRequestException(str(e))

        if start_date > end_date:
            raise BadRequestException(
                "Start date {start} must be before end {end} date.".format(
                    start=start_date, end=end_date
                )
            )

        return start, end

    def _queryset(self, start: date, end: date) -> QuerySet:
        """generate a queryset for the date range"""

        return self.model.objects.filter(
            **{
                "%s__gte" % self.date_column: start,
                "%s__lt" % self.date_column: end + timedelta(days=1),
            }
        ).prefetch_related(*self.prefetch_related)

    def csv_columns(self) -> Optional[Sequence[str]]:
        """if the csv columns cannot be determined from the first row"""
        pass

    def to_csv(self, rows: Generator[Mapping[str, str], Any, Any]) -> Generator[str, None, None]:
        """serialize the given objects into csv file lines"""
        writer = None

        for row in rows:
            if not writer:
                columns = self.csv_columns() or list(row.keys())
                writer = csv.DictWriter(StreamingEchoBuffer(), columns)
                yield writer.writeheader()
            yield writer.writerow(row)

    def to_json(self, rows: Generator[Mapping[str, str], Any, Any]) -> Generator[str, None, None]:
        """serialize the given objects into json file lines"""
        first = True

        for row in rows:

            # hack, hack, manual json out put, but we want to stream an this seems safe, right?
            if first:
                first = False
                yield "["
            else:
                yield ","
            yield json.dumps(row)

        yield "]"

    def negotiate(self, samples, accept: str = "text/csv") -> Generator[str, None, None]:
        """negotiate the correct content type as indicated by the client via the ACCEPT header.

        right now we only support "text/csv".
        """

        if accept in self.MIME_TYPES_CSV:
            return self.MIME_TYPES_CSV[0], self.to_csv(samples)

        return self.MIME_TYPES_JSON[0], self.to_json(samples)


class SampleExportApiMixin(SimpleRestAPISupport):
    """ """

    model = PriceSample
    date_column = "timestamp"
    prefetch_related = [
        "page",
        "agent",
        "agent__browser",
        "agent__device",
        "agent__os",
        "location",
        "location__city",
        "location__city__country",
    ]

    def serialize(self, sample: PriceSample) -> Mapping[str, str]:
        """serialize the object"""
        return {
            "id": sample.id,
            "timestamp": sample.timestamp.isoformat(),
            "url": sample.page.url,
            "price": sample.price,
            "currency": sample.currency,
            "uuid": sample.uuid,
            "browser": sample.agent.browser.name,
            "browser_version": sample.agent.browser.version,
            "device": sample.agent.device.name,
            "device_brand": sample.agent.device.brand,
            "device_version": sample.agent.device.version,
            "os": sample.agent.os.name,
            "postal_code": sample.location.postal_code,
            "geonames_city_id": sample.location.city.geonameid,
            "country": sample.location.city.country.iso_code,
        }

    def samples(
        self, start_date: str = None, end_date: str = None
    ) -> Generator[PriceSample, None, None]:
        """stream a list of samples in the given daterange"""
        start, end = self._validate_date_range(start_date, end_date)
        qs = self._queryset(start, end)

        for sample in qs:
            yield self.serialize(sample)


class PersonsExportApiMixin(SimpleRestAPISupport):
    """ """

    model = Person
    date_column = "created"
    prefetch_related = ["attributes"]

    def csv_columns(self) -> Optional[Sequence[str]]:
        """if the csv columns cannot be determined from the first row"""
        attr_names = list(
            PersonalAttribute.objects.order_by().values_list("name", flat=True).distinct()
        )
        attr_names.extend(["uuid", "created", "updated"])
        return attr_names

    def serialize(self, person: Person) -> Mapping[str, str]:
        """serialize the object"""
        data = {
            "uuid": person.uuid,
            "created": person.created.isoformat(),
            "updated": person.created.isoformat(),
        }

        attributes = {}
        for attr in person.attributes.all():
            display_name = attr.value_name.name if attr.value_name else None
            attributes.setdefault(attr.name, []).append(
                {
                    "value": attr.value,
                    "display_name": display_name,
                }
            )

        for key, value in attributes.copy().items():
            if len(value) == 1:
                attributes[key] = value[0]

        data.update(attributes)
        return data

    def samples(
        self, start_date: str = None, end_date: str = None
    ) -> Generator[PriceSample, None, None]:
        """stream a list of samples in the given daterange"""
        start, end = self._validate_date_range(start_date, end_date)
        qs = self._queryset(start, end)

        for sample in qs:
            yield self.serialize(sample)
