# -*- coding: utf-8 -*-

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

# XPATH expression to identify the continuation button
STEPNEXT_BUTTON = "//button[@onclick=\"AjaxSetRequestNextStep\"]"

# Names of useful attributes in a calendar
DAY_ATTRIB = "data-day"
MONTH_ATTRIB = "data-month"
YEAR_ATTRIB = "data-year"

# A substring in the `class` attribute value of a date element that indicates that the day is available
STATE_AVAILABLE = "state-aa"
