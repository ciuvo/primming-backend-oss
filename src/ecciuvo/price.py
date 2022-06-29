# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import logging
import re
from decimal import Decimal
from functools import reduce

from .currencies import CURRENCIES

log = logging.getLogger(__name__)

AMOUNT_FILTER = re.compile(
    r"(\d+\u20ac\d{1,2}|\d[\s\d\xa0\uffa0\ufeff\u202f,.]+|\d)", re.I | re.M | re.U
)


def parse_currency(value):
    for c in [c.code for c in CURRENCIES if c.match.search(value)]:
        log.debug("Parsed currency <%s> from <%s>", c, value)
        return c
    log.debug("Could not parse currency from string: <%s>", value)
    return None


def parse_amount_from(value):
    """Tries to parse an amount (digits w/ optional decimal comma and thousand
    seperator). The amount is represented as an integer (the actual value times
    100).
    It makes educated guesses about the semantic of comma and dot.

    Parameters
    ----------
    value : str
        The string that might contain a price that should be extracted.

    Returns
    -------
    amount : int or None
        The extracted amount in cents. None if no amount could be extracted.

    Example
    -------
    >>> parse_amount_from(u'$10 off')
    1000
    >>> parse_amount_from(u'$1,00')
    100
    >>> parse_amount_from(u'$1,000')
    100000
    >>> parse_amount_from(u'129,90000001')
    12990
    >>> parse_amount_from(u'574€83')
    57400
    >>> parse_amount_from(u'€ 2.74')
    274
    >>> parse_amount_from(u'132,20 €')
    13220
    """
    digits = AMOUNT_FILTER.search(value).group()
    digits = re.sub(r"\s|\xa0|\uffa0|\ufeff|\u202f", "", digits, re.U)

    # split price string at "," and "." - last part
    # are the fractional digits
    vsplit = re.split(r"[,\.\u20ac]", digits, re.U)
    if len(vsplit) == 1:
        vv = vsplit[0]
    # TODO: prove that this heuristic applies to all currencies
    elif len(vsplit[-1]) > 2 and len(vsplit[-1]) < 6:
        vv = "".join(vsplit)
    else:
        dec = reduce(lambda x, y: x + y, vsplit[:-1])
        frac = vsplit[-1]
        vv = dec + "." + frac

    price = int(Decimal(vv) * 100)
    return price


def clean_price(scraped_price, scraped_currency=None, default_currency="EUR"):
    """clean the price as scraped from the website

    :returns: a tuple of the price in cents + the currency
    """

    # deal with currency
    if scraped_currency:
        currency = parse_currency(scraped_currency)
    else:
        currency = default_currency

    price = parse_amount_from(scraped_price)
    if not price or price > 2147483647 or price < 0:
        raise ValueError("Price out of range: %s" % scraped_price)

    return price, currency
