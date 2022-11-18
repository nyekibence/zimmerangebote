#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from logging import Logger
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Iterable, Union, Optional, Mapping, Sequence

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from zimmerangebote import settings
from zimmerangebote.utils import (
    Room,
    ThreadResultHolder,
    get_custom_logger,
    get_ngrams,
    shift_date_by_months,
    fill_scheme_string
)


def configure_driver() -> webdriver.Chrome:
    """Configure the Chrome driver for selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def find_and_click(
        driver: webdriver.Chrome,
        xpath_expr: str,
        wait_secs: int = 10
) -> WebElement:
    """Find an element and click on it.

    Args:
        driver: The currently used Chrome driver.
        xpath_expr: An XPATH expression to identify the element.
        wait_secs: Specifies how long to wait to find the clickable
            element in seconds. Default: `10`.

    Returns:
         The selected element after clicking on it.
    """
    element = WebDriverWait(driver, wait_secs).until(
        EC.presence_of_element_located((By.XPATH, xpath_expr))
    )
    driver.execute_script("arguments[0].click();", element)
    return element


def select_elements(
        driver: webdriver.Chrome,
        xpath_expr: str,
        wait_secs: int = 10
) -> List[WebElement]:
    """Find multiple elements.

    Args:
        driver: The currently used Chrome driver.
        xpath_expr: An XPATH expression to identify the elements.
        wait_secs: Specifies how long to wait to find the elements
            in seconds. Default: `10`.

    Returns:
        The list of elements that were found.
    """
    elements = WebDriverWait(driver, wait_secs).until(
        EC.presence_of_all_elements_located((By.XPATH, xpath_expr))
    )
    return elements


def _is_day_available(element: WebElement) -> bool:
    """Check if an elements that represents a day is available for booking."""
    return element.find_element(By.XPATH, "..").get_attribute(
        "class").endswith(settings.STATE_AVAILABLE)


def select_stay(days: Iterable[WebElement]) -> Union[None, Tuple[WebElement, date]]:
    """Select the date of a 1-day stay.

    Args:
        days: Elements representing days.

    Returns:
        A tuple of 2 objects: the date of arrival as a web element
        and the date of departure as a `date` object. If there is no
        available time interval, the return value will be `None`.
    """
    available_days = sorted(
        filter(_is_day_available, days),
        key=lambda x: int(x.get_attribute(settings.DAY_ATTRIB))
    )
    selected_days = None
    for bigram in get_ngrams(available_days, 2):
        left, right = bigram
        if int(left.get_attribute(settings.DAY_ATTRIB)) == int(right.get_attribute(settings.DAY_ATTRIB)) - 1:
            departure_date = date(
                day=int(right.get_attribute(settings.DAY_ATTRIB)),
                month=int(right.get_attribute(settings.MONTH_ATTRIB)),
                year=int(right.get_attribute(settings.YEAR_ATTRIB))
            )
            selected_days = (left, departure_date)
            break
    return selected_days


def click_stay_dates(
        driver: webdriver.Chrome, *,
        arrival: WebElement,
        departure: date,
        wait_secs: int = 10,
        logger: Optional[Logger] = None
) -> WebElement:
    """Click on selected days. This is a side effect function,
    it modifies the driver state.

    Args:
        driver: The currently used Chrome driver.
        arrival: The arrival date element.
        departure: The departure date as a `date` object.
        wait_secs: Specifies how long to wait to find the
            departure element in seconds. Default: `10`.
        logger: Optional. A logger that will write debug messages.

    Returns:
        The departure element.
    """
    driver.execute_script("arguments[0].click();", arrival)
    if logger is not None:
        logger.debug("Arrival clicked.")

    date_expr = fill_scheme_string(
        scheme=settings.DEPARTURE_SCHEME,
        year=departure.year,
        month=departure.month,
        day=departure.day
    )
    departure_element = WebDriverWait(driver, wait_secs).until(
        EC.element_to_be_clickable((By.XPATH, date_expr))
    )
    if logger is not None:
        logger.debug(f"Departure element found: "
                     f"{departure_element.get_attribute('data-original-title')}")

    driver.execute_script("arguments[0].click();", departure_element)
    if logger is not None:
        logger.debug("Departure clicked.")

    return departure_element


def collect_room_properties(
        room_element: WebElement,
        n_months: int,
        num_regex: re.Pattern = re.compile("\d+"),
) -> Room:
    """Collect the properties of a room:
    category, size, price, booking period (early or not).
    Request date will be filled added automatically.

    Args:
        room_element: A web element whose children contain all the
            necessary information about the room.
        n_months: The number of month between the current date and the
            arrival date. If it is at least 6 month, the booking will
            be considered early.
        num_regex: A regex to identify numbers in the room price and
            size strings. Default: `'\d+'`.

    Returns:
        The room data as a `Room` object.
    """
    is_early = 6 <= n_months
    category = room_element.find_element(By.XPATH, settings.ROOM_CAT_XPATH).text
    size = room_element.find_element(By.XPATH, settings.ROOM_SIZE_XPATH).text
    price = room_element.find_element(By.XPATH, settings.ROOM_PRICE_XPATH).text

    size = int(num_regex.search(size).group())
    price = int(num_regex.search(price).group())
    return Room(
        category=category,
        size=size,
        price=price,
        is_early_booking=is_early
    )


def create_room_table(records: Sequence[Mapping[str, Union[str, int, bool]]]) -> pd.DataFrame:
    """Create and rearrange a table from the room records provided as mappings."""
    room_df: pd.DataFrame = pd.DataFrame.from_records(records)

    # Sort values by price. Get the cheapest for each `(category, size) group.`
    room_df = room_df.sort_values("price").groupby(["category", "size"]).first().reset_index()

    # Reorder the columns if necessary so that `date` be the first column
    cols = room_df.columns.tolist()
    datum_index = cols.index("datum")
    if datum_index != 0:
        del cols[datum_index]
        cols.insert(0, "datum")
        room_df = room_df[cols]

    # Replace column names and `is_early_booking` column values with German words
    room_df["is_early_booking"] = room_df["is_early_booking"].map(settings.EARLY_BOOKING_MAP)
    room_df = room_df.rename(columns=settings.COL_NAME_MAP)
    return room_df


def scrape_room_data(
        browser: webdriver.Chrome,
        month_shift: int,
        target: ThreadResultHolder,
) -> None:
    """Scrape the data describing available rooms in a specific month.

    Args:
        browser: An initialized Chrome browser.
        month_shift: Specifies how many months to move forward from the
            current month to get the target time interval.
        target: A mutable dataclass with a `df` attribute. The result of
            this function will be assigned to it.
    """
    assert 1 <= month_shift, f"month_shift must be a positive integer, got {month_shift}"
    logger = get_custom_logger(f"{__name__}-in{month_shift}months")

    browser.get(settings.BASE_URL)
    logger.debug(f"URL {settings.BASE_URL} opened.")

    target_date = shift_date_by_months(month_shift)
    if 2 < month_shift:
        find_and_click(
            driver=browser,
            xpath_expr=settings.MONTH_SELECTOR
        )
        logger.debug(f"Month menu opened.")
        find_and_click(
            driver=browser,
            xpath_expr=fill_scheme_string(
                scheme=settings.AJAX_MONTH_SCHEME,
                year=target_date.year,
                month=target_date.month
            )
        )
        logger.debug(f"Month ({target_date.month}, {target_date.year}) selected.")

    days_xpath = fill_scheme_string(
        scheme=settings.CALENDAR_DAY_SCHEME,
        year=target_date.year,
        month=target_date.month
    )
    days = select_elements(browser, days_xpath)
    stay = select_stay(days)
    if stay is None:
        logger.info("No matching date found.")
        return
    arrival, departure = stay
    arrival_month = arrival.get_attribute(settings.MONTH_ATTRIB)
    arrival_day = arrival.get_attribute(settings.DAY_ATTRIB)
    logger.debug(f"Dates {arrival_day}.{arrival_month} and "
                 f"{departure.day}.{departure.month} selected.")
    click_stay_dates(
        browser,
        arrival=arrival,
        departure=departure,
        logger=logger
    )
    logger.debug("Loading offers...")
    browser.execute_script(settings.STEPNEXT_FUNC)
    room_elements = select_elements(browser, settings.ROOM_XPATH)
    logger.debug(f"Number of room elements: {len(room_elements)}")
    room_df = create_room_table(
        [collect_room_properties(room_element, month_shift).to_dict() for room_element in room_elements]
    )
    target.df = room_df

def main() -> None:
    """Main function"""
    browsers = (configure_driver(), configure_driver())
    month_shifts = (1, 6)
    short_term, early = ThreadResultHolder(), ThreadResultHolder()

    with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        executor.map(scrape_room_data, browsers, month_shifts, [short_term, early])
    [browser.quit() for browser in browsers]

    if short_term.df is None and early.df is not None:
        table = early.df
    elif short_term.df is not None and early.df is None:
        table = short_term.df
    elif short_term.df is not None and early.df is not None:
        table = pd.concat((short_term.df, early.df), ignore_index=True)
    else:
        print("No rooms found :(")
        return
    print(table.to_csv(index=False))


if __name__ == "__main__":
    main()
