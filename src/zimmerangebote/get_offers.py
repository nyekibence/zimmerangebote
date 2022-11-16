#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from logging import Logger
from typing import List, Tuple, Iterable, Union, Optional
from datetime import date

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import ActionChains

from zimmerangebote import settings
from zimmerangebote.utils import (
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
        action_chain: Optional[ActionChains] = None,
        wait_secs: int = 10
) -> WebElement:
    """Find an element and click on it.

    Args:
        driver: The currently used Chrome driver.
        xpath_expr: An XPATH expression to identify the element.
        action_chain: Optional. An `ActionChain` object to perform actions on the page.
            If unspecified, the driver will be called directly.
        wait_secs: Specifies how long to wait to find the clickable
            element in seconds. Default: `10`.

    Returns:
         The selected element after clicking on it.
    """
    element = WebDriverWait(driver, wait_secs).until(
        EC.presence_of_element_located((By.XPATH, xpath_expr))
    )
    if action_chain is not None:
        action_chain.move_to_element(element).click().perform()
    else:
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
        action_chain: Optional[ActionChains] = None,
        wait_secs: int = 10,
        logger: Optional[Logger] = None
) -> WebElement:
    """Click on selected days. This is a side effect function,
    it modifies the driver state.

    Args:
        driver: The currently used Chrome driver.
        arrival: The arrival date element.
        departure: The departure date as a `date` object.
        action_chain: Optional. An `ActionChain` object to perform actions on the page.
            If unspecified, the driver will be called directly.
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

    if action_chain is not None:
        action_chain.move_to_element(departure_element).click().perform()
    else:
        driver.execute_script("arguments[0].click();", departure_element)
    if logger is not None:
        logger.debug("Departure clicked.")

    return departure_element


def main() -> None:
    """Main function"""
    logger = get_custom_logger(__name__)
    browser = configure_driver()
    action_chain = ActionChains(browser)
    browser.get(settings.BASE_URL)
    logger.debug(f"URL {settings.BASE_URL} opened.")

    target_date = shift_date_by_months(6)
    find_and_click(
        driver=browser,
        action_chain=action_chain,
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
    if stay is not None:
        arrival, departure = stay
        arrival_month = arrival.get_attribute(settings.MONTH_ATTRIB)
        arrival_day = arrival.get_attribute(settings.DAY_ATTRIB)
        logger.debug(f"Dates {arrival_day}.{arrival_month} and "
                     f"{departure.day}.{departure.month} selected")
        click_stay_dates(
            browser,
            arrival=arrival,
            departure=departure,
            logger=logger
        )
    else:
        logger.info("No matching date found.")
    find_and_click(browser, settings.STEPNEXT_BUTTON)
    browser.quit()


if __name__ == "__main__":
    main()
