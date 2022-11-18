# -*- coding: utf-8 -*-

from types import MappingProxyType

"""A settings file that contains constants for scraping a dynamic website."""

# The base URL
BASE_URL = "https://www.linsbergasia.at/websline-abm/homepage/booking/index/de"

# XPATH expression to identify the month menu
MONTH_SELECTOR = "//button[@class=\"btn btn-default btn-block dropdown-toggle\"]"

# XPATH expression scheme to identify a month table in a calendar
AJAX_MONTH_SCHEME = "//a[@onclick=\"AjaxCalendarSet({year}, {month});return false;\"]"

# XPATH expression scheme to identify a concrete day in a calendar
CALENDAR_DAY_SCHEME = "//div[@data-original-title and @class=\"abm-calendar-day\" and " \
                      "@data-month=\"{month}\" and @data-year=\"{year}\"]"

# XPATH expression scheme to identify a departure day
DEPARTURE_SCHEME = "//div[@class=\"abm-calendar-day\" and @data-month=\"{month}\" and " \
                   "@data-year=\"{year}\" and @data-day=\"{day}\" and " \
                   "contains(@data-original-title, 'Abreisedatum')]"

# Names of useful attributes in a calendar
DAY_ATTRIB = "data-day"
MONTH_ATTRIB = "data-month"
YEAR_ATTRIB = "data-year"

# A substring in the `class` attribute value of a date element that indicates that the day is available
STATE_AVAILABLE = "state-aa"

# Script to execute click on the continuation button
STEPNEXT_FUNC = "AjaxSetRequestStepNext();"

# XPATH expression to identify a room element
ROOM_XPATH = "//div[contains(@class, 'row abm-room') and " \
             "@data-roomid and @data-requestid]"

# XPATH expressions to look up room category, size and price
ROOM_CAT_XPATH = ".//div/h4[@class=\"abm-headline\"]"
ROOM_SIZE_XPATH = ".//p/span[@class=\"h4\"]"
ROOM_PRICE_XPATH = ".//p[@class and @onclick]/span[@class=\"h2\"]"

# Column names in the output table mapped to the data fields of a `zimmerangebote.utils.Room` object
COL_NAME_MAP = MappingProxyType({
    "datum": "Datum",
    "category": "Kategorie",
    "price": "Preis",
    "size": "Zimmergröße (m\u00b2)",
    "is_early_booking": "Buchungszeitraum"
})

# Readable strings indicating whether a booking is early
EARLY_BOOKING_MAP = MappingProxyType({
    False: "Kurzfristig",
    True: "Frühbuchung"
})
