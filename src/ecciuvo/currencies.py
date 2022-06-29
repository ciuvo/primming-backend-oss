# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
# -*- coding: utf-8 -*-
#
# Copyright 2009-2016 Ciuvo GmbH. All rights reserved. This file is subject to the terms and
# conditions defined in file 'LICENSE', which is part of this source code package.

"""
.. codeauthor:: Mathias Ertl <mati@ciuvo.com>
"""

import re

MATCH_REGISTRY = set()
TEMPLATE_SYMBOL_SUCCEEDS = 0
TEMPLATE_SYMBOL_PRECEDES = 1


class Currency(object):
    __slots__ = (
        "code",
        "label",
        "match",
        "symbol",
        "decimal",
        "grouping",
        "places",
        "csp",
        "additional_symbols",
        "translator",
        "html_format",
        "separator",
    )

    def __init__(
        self,
        code,
        symbol=None,
        decimal=".",
        grouping=",",
        places=2,
        csp=TEMPLATE_SYMBOL_PRECEDES,
        symbol_match=True,
        additional_symbols=None,
        match=None,
        label=None,
        separator=" ",
    ):
        global MATCH_REGISTRY

        # set default values:
        symbol = symbol or code
        additional_symbols = additional_symbols or []

        if match is None:
            matches = set(m.lower() for m in [code] + additional_symbols)
            if symbol_match:
                matches.add(symbol.lower())

            if matches & MATCH_REGISTRY:
                matches = ", ".join(matches & MATCH_REGISTRY)
                raise RuntimeError(
                    "%s: Symbols already matched by other currencies: %s" % (code, matches)
                )

            MATCH_REGISTRY |= matches
            match = "|".join(re.escape(m) for m in matches)

        self.code = code
        self.label = label or code
        self.match = re.compile(match, re.I | re.M | re.U)
        self.symbol = symbol
        self.decimal = decimal
        self.grouping = grouping
        self.places = places
        self.csp = csp
        self.additional_symbols = additional_symbols
        self.translator = {ord("."): self.decimal, ord(","): self.grouping}
        self.html_format = re.compile(r"(\%s)(\d{%d})" % (self.decimal, self.places))
        self.separator = separator

    def format(self, value, places=None, html=False):
        if places is None:
            places = self.places

        if not places:
            value = int(value)
            pattern = "{:,d}"
        else:
            pattern = "{:,.0%df}" % places

        # Format our value, replace decimal and grouping symbol
        result = pattern.format(value).translate(self.translator)

        # Add currency symbol
        if self.csp == TEMPLATE_SYMBOL_SUCCEEDS:
            result = self.separator.join((result, self.symbol))
        else:
            result = self.separator.join((self.symbol, result))

        # If the caller requests html, add the <sup> tags to the result
        if html and places:
            result = self.html_format.sub(r"\1<sup>\2</sup>", result)
        return result

    def __hash__(self):
        return hash(self.code)


CURRENCIES = (
    # Most important/frequent currencies go first (match early!)
    Currency(
        "EUR",
        "€",
        decimal=",",
        grouping=".",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        additional_symbols=["&euro;"],
        label="Euro",
    ),
    Currency("USD", "$", match=r"USD|(([^R]|^)\$)", label="US Dollar", separator=""),
    Currency("GBP", "£", additional_symbols=["&pound;"], label="British Pound", separator=""),
    Currency("BRL", "R$", decimal=",", grouping=".", label="Brasilian Real"),
    Currency(
        "PLN",
        "zł",
        decimal=",",
        grouping=" ",
        label="Polish Złoty",
        separator=" ",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
    ),
    Currency(
        "RUB",
        "руб.",
        decimal=",",
        grouping=" ",
        places=0,
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        label="Russian Rubel",
        additional_symbols=["₽", "руб"],
    ),
    Currency(
        "UAH",
        "грн.",
        decimal=",",
        grouping=" ",
        places=0,
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        label="Ukrainian Hryvnia",
        additional_symbols=["грн"],
    ),
    Currency("AUD", "$", symbol_match=False, label="Australian Dollar", separator=""),
    Currency("CAD", "CDN$", match=r"CAD|C\s*\$|CND|CDN\s*\$", label="Canadian Dollar"),
    Currency("INR", "₹", places=0, additional_symbols=["RS."], label="Indian Rupee", separator=""),
    Currency(
        "CHF",
        "CHF",
        decimal=",",
        grouping=".",
        additional_symbols=["FR"],
        label="Frances",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
    ),
    Currency("CZK", "Kč", decimal=",", grouping=" ", label="Czeck Koruna"),
    Currency("DKK", "kr.", decimal=",", grouping=".", places=0, label="Danish Krona"),
    Currency(
        "SEK",
        "kr",
        decimal=",",
        grouping=" ",
        places=0,
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        label="Swedish Krona",
    ),
    Currency("HUF", "Ft", label="Hungarian Forint"),
    Currency("MXN", "Mex$", label="Mexican Peso"),
    Currency(
        "NOK",
        "kr",
        decimal=",",
        grouping=".",
        places=0,
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        symbol_match=False,
        label="Norwegian Krown",
    ),
    Currency(
        "TRY",
        "₺",
        decimal=",",
        grouping=".",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        additional_symbols=["TL"],
        label="New Turkish Lira",
        separator="",
    ),
    Currency(
        "RON",
        "lei",
        decimal=",",
        grouping=".",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        label="Rumanian Leu",
    ),
    Currency("RSD", "РСД", decimal=",", grouping=".", label="Serbian Dinar"),
    # Exotic / Lower priority
    Currency("AED", "ﺩ.ﺇ.", decimal="٫", grouping="٬", label="UAE Dirham"),
    Currency("AOA", "Kz", label="Angolan Kwanza"),
    Currency("ANG", "ƒ", decimal="٫", grouping=" ", label="Dutch Guilder"),
    Currency("ALL", "ALL", csp=TEMPLATE_SYMBOL_SUCCEEDS, label="Albanian Lek"),
    Currency("AMD", "֏", label="Armenian Dram"),
    Currency("ARS", "$", decimal=",", grouping=".", symbol_match=False, label="Argentine Peso"),
    Currency("AWG", "Afl.", decimal=",", grouping=" ", label="Aruban florin"),
    Currency("AZN", "ман", label="Azerbaijani New Manat"),
    Currency("BAM", "KM", decimal=",", grouping=".", label="Bosnian Mark"),
    Currency("BBD", "$", symbol_match=False, label="Barbadian Dollar", separator=""),
    Currency("BDT", "Tk", label="Bangladeshi Taka"),
    Currency("BGN", "лв.", decimal=",", grouping=".", label="Bulgarian Lev"),
    Currency("BHD", ".ﺩ.ﺏ", decimal="٫", grouping="٬", places=3, label="Bahraini Dinar"),
    Currency("BND", "$", symbol_match=False, label="Bruneian Dollar", separator=""),
    Currency("BOB", "$b", decimal=",", grouping=" ", label="Bolivian Bolíviano"),
    Currency("BSD", "$", symbol_match=False, label="Bahamian Dollar", separator=""),
    Currency("BYN", "Br", label="Belarusian Ruble"),
    Currency("BZD", "BZ$", label="Belizean Dollar"),
    Currency("BIF", "FBu", label="Burundian Franc"),
    Currency(
        "CLP",
        "$",
        decimal=",",
        grouping=".",
        places=0,
        symbol_match=False,
        label="Chilean Peso",
        separator="",
    ),
    Currency(
        "CLF",
        "UF",
        decimal=",",
        grouping=".",
        places=0,
        symbol_match=False,
        label="Unidad de Fomento",
        separator="",
    ),
    Currency(
        "CNY",
        "￥",
        symbol_match=False,
        additional_symbols=["元", "圆"],
        label="Chinese Renminbi",
    ),
    Currency(
        "COP",
        "$",
        decimal=",",
        grouping=".",
        symbol_match=False,
        label="Columbian Peso",
        separator="",
        additional_symbols=["COU"],
    ),
    Currency("CRC", "₡", decimal=",", grouping=".", label="Costa Rican Colón"),
    Currency("CUP", "₱", symbol_match=False, additional_symbols=["$", "$MN"], label="Cuban Peso"),
    Currency("DOP", "RD$", decimal=",", grouping=".", symbol_match=False, label="Dominican Peso"),
    Currency(
        "DZD",
        "ﺪﺟ",
        decimal=",",
        grouping=".",
        places=0,
        additional_symbols=["ﺩ.ﺝ."],
        label="Algerian Dinar",
    ),
    Currency(
        "EGP",
        "ﺝ.ﻡ.",
        decimal="٫",
        grouping="٬",
        places=3,
        additional_symbols=["E£", "E&pound;"],
        label="Egyptian Pound",
    ),
    Currency(
        "ETB",
        "Br",
        decimal=",",
        grouping=" ",
        additional_symbols=["ብር"],
        symbol_match=False,
        label="Egyptian Pound",
    ),
    Currency("FJD", "$", symbol_match=False, label="Fijian Dollar", separator=""),
    Currency("GEL", "ლ", additional_symbols=["₾", "GEL"], label="Georgian Lari"),
    Currency("GMD", "D", label="Gambian Dalasi"),
    Currency("GTQ", "Q", label="Guatemalan Quetzal"),
    Currency("HKD", "HK$", label="Hong Kong Dollar"),
    Currency("HNL", "L", decimal=",", grouping=".", label="Honduran lempira"),
    Currency("HRK", "kn", decimal=",", grouping=".", label="Croatian Kuna"),
    Currency("IDR", "Rp", places=0, label="Indonesian Rupiah"),
    Currency("ILS", "₪", label="Israeli Shekel"),
    Currency("IRR", "﷼", decimal="٫", grouping="٬", places=0, label="Iranian Rial"),
    Currency("ISK", "Íkr", label="Icelandic króna"),
    Currency("JMD", "J$", csp=TEMPLATE_SYMBOL_PRECEDES, label="Jamaican Dollar"),
    Currency("JOD", "ﺩ.ﺃ.", decimal="٫", grouping="٬", label="Jordan Dinar"),
    Currency("JPY", "￥", additional_symbols=["¥", "円", "圓"], label="Japanese Yen", places=0),
    Currency("KES", "KSh", csp=TEMPLATE_SYMBOL_SUCCEEDS, label="Kenyan Shilling"),
    Currency("KRW", "₩", label="South Korean Wong"),
    Currency(
        "KWD",
        "ﺩ.ﻙ",
        decimal="٫",
        grouping="٬",
        places=3,
        additional_symbols=["K.D."],
        label="Kuwaiti Dinar",
    ),
    Currency("KHR", "៛", label="Cambodian riel"),
    Currency("KYD", "$", symbol_match=False, label="Caymanian Dollar", separator=""),
    Currency("KZT", "₸", decimal=",", grouping=" ", label="Kazakhstani Tenge"),
    Currency("LAK", "₭", label="Laotian Kip"),
    Currency("LKR", "රු", additional_symbols=["ரூ"], label="Sri Lankan Rupee"),
    Currency("LTL", "Lt", label="Lithuanian Litas"),
    Currency("LBP", "ل.ل", decimal="٫", grouping="٬", label="Lebanese Pound"),
    Currency("LYD", "ﻝ.ﺩ", label="Lybian Dinar"),
    Currency("MAD", "ﺩ.ﻡ.", label="Maroccan Dirham"),
    Currency("QAR", "ر.ق", label="Qatari riyal"),
    Currency("MDL", decimal=",", grouping=".", label="Moldawian Leu"),
    Currency("MKD", "ден", label="Makedonian Denar"),
    Currency("MOP", "MOP$", label="Macau Pataca"),
    Currency("MYR", "RM", label="Malaysian Ringgit"),
    Currency("MMK", "K", label="Burmese Kyat"),
    Currency("MNT", "₮", label="Mongolian tögrög"),
    Currency("MGA", "Ar", decimal=",", grouping=" ", label="Malagasy Ariary"),
    Currency("NAD", "N$", grouping=" ", label="Namibian Dollar"),
    Currency("NGN", "₦", label="Nigerian Naira"),
    Currency("NIO", "C$", decimal=",", symbol_match=False, label="Nicaraguan Córdoba"),
    Currency(
        "NPR",
        "रू.",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        additional_symbols=["₨", "नेरू"],
        label="Nepalese Rupee",
    ),
    Currency(
        "NZD", "$", grouping=".", symbol_match=False, label="New Zealand Dollar", separator=""
    ),
    Currency("OMR", "ﺭ.ﻉ.", decimal="٫", grouping="٬", places=3, label="Omani Rial"),
    Currency("PAB", "B/.", decimal=",", grouping=" ", label="Panamanian Balboa"),
    Currency("PEN", "S/.", csp=TEMPLATE_SYMBOL_SUCCEEDS, label="Peruvian Sol"),
    Currency("PHP", "₱", label="Philippine Peso"),
    Currency("PKR", "Rs", csp=TEMPLATE_SYMBOL_SUCCEEDS, label="Pakistani rupee"),
    Currency("PYG", "₲", csp=TEMPLATE_SYMBOL_SUCCEEDS, label="Paraguayan guaraní"),
    Currency(
        "RWF",
        "R₣",
        decimal=",",
        grouping=" ",
        additional_symbols=["FRw", "RF"],
        label="Rwandan Franc",
    ),
    Currency("SAR", "ﺭ.ﺱ", decimal="٫", grouping="٬", places=0, label="Saudi Riyal"),
    Currency("SGD", "S$", csp=TEMPLATE_SYMBOL_PRECEDES, label="Singapur Dollar", separator=""),
    Currency("SRD", "$", symbol_match=False, label="Surinamese Dollar", separator=""),
    Currency("THB", "฿", places=0, label="Thai Baht"),
    Currency("TZS", "TSh", csp=TEMPLATE_SYMBOL_SUCCEEDS, places=0, label="Tanzanian shilling"),
    Currency("TND", "ﺩ.ﺕ.", decimal=",", grouping=".", places=3, label="Tunesian Dinar"),
    Currency("TWD", "NT$", csp=TEMPLATE_SYMBOL_SUCCEEDS, label="Taiwan Dollar"),
    Currency("UYU", "$U", csp=TEMPLATE_SYMBOL_PRECEDES, label="Uruguayan Peso"),
    Currency(
        "VEF",
        "Bs.",
        decimal=",",
        grouping=".",
        csp=TEMPLATE_SYMBOL_PRECEDES,
        label="Venezuelan Bolivar",
    ),
    Currency(
        "VND",
        "₫",
        decimal=",",
        grouping=".",
        places=0,
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        additional_symbols=["đồng"],
        label="Vietnamese Dong",
    ),
    Currency("WST", "$", symbol_match=False, label="Samoan Tala", separator=""),
    Currency("XAF", "CFA", csp=TEMPLATE_SYMBOL_SUCCEEDS, label="CFA Franc (Cent.)"),
    Currency("XCD", "$", symbol_match=False, label="East Caribbean Dollar", separator=""),
    Currency(
        "XOF",
        "CFA",
        decimal="٫",
        grouping="٬",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        symbol_match=False,
        label="CFA Franc (West.)",
    ),
    Currency(
        "XPF",
        "CFP",
        decimal="٫",
        grouping="٬",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        symbol_match=False,
        label="CFP Franc",
    ),
    Currency(
        "YER",
        "﷼",
        decimal=".",
        grouping=",",
        csp=TEMPLATE_SYMBOL_SUCCEEDS,
        symbol_match=False,
        label="Yemeni rial",
    ),
    Currency(
        "ZAR", "R", symbol_match=False, decimal=",", grouping=" ", label="South African Rand"
    ),
)

SUPPORTED_CURRENCIES = set([c.code for c in CURRENCIES])

# A dictionary of currency codes plus some aliases:
CURRENCY_INDEX = {c.code: c for c in CURRENCIES}
CURRENCY_INDEX["РУБ"] = CURRENCY_INDEX["RUB"]
