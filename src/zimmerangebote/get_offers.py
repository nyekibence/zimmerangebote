#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import expanduser
from typing import List, Tuple, Iterable, Union, Optional
from datetime import date
from dateutil.relativedelta import relativedelta
from itertools import islice, tee

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

def shift_date_by_months(n_months: int) -> date:
    """Add `n_month` to the current date.

    Args:
        n_months: The number of month to add to the current date.

    Returns:
        The calculated future date.
    """
    return date.today() + relativedelta(months=n_months)


def configure_driver() -> webdriver.Chrome:
    """Configure the Chrome driver for selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    homedir = expanduser("~")
    webdriver_service = Service(f"{homedir}/chromedriver/stable/chromedriver")
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    return driver


def find_and_click(
        driver: webdriver.Chrome,
        xpath_expr: str,
        wait_secs: int = 5
) -> WebElement:
    """Find an element and click on it.

    Args:
        driver: The currently used Chrome driver.
        xpath_expr: An XPATH expression to identify the element.
        wait_secs: Specifies how long to wait to find the clickable
            element in seconds. Default: `5`.

    Returns:
         The selected element after clicking on it.
    """
    element = WebDriverWait(driver, wait_secs).until(
        EC.element_to_be_clickable((By.XPATH, xpath_expr))
    )
    element.click()
    return element


def make_xpath_for_days(year: int, month: int) -> str:
    """Create an XPATH expression to select bookable days."""
    return f"//div[@class=\"abm-calendar-day\" and @data-month={month} and @data-year={year}]"


def select_elements(
        driver: webdriver.Chrome,
        xpath_expr: str,
        wait_secs: int = 5
) -> List[WebElement]:
    """Find multiple elements.

    Args:
        driver: The currently used Chrome driver.
        xpath_expr: An XPATH expression to identify the elements.
        wait_secs: Specifies how long to wait to find the elements
            in seconds. Default: `5`.

    Returns:
        The list of elements that were found.
    """
    elements = WebDriverWait(driver, wait_secs).until(
        EC.presence_of_all_elements_located((By.XPATH, xpath_expr))
    )
    return elements


def _is_day_available(element: WebElement) -> bool:
    """Check if an elements that represents a day is available for booking."""
    return element.find_element(By.XPATH, "..").get_attribute("class").endswith("state-aa")


def get_ngrams(
        elements: Iterable,
        ngram_length: int,
        step: Optional[int] = None
) -> Iterable[Tuple]:
    """An efficient ngram iterator based on
    https://github.com/dlazesz/n-gram-benchmark/blob/master/ngram.py

    Args:
        elements: The elements to iterate over.
        ngram_length: The ngram length (e. g. 2 means bigrams).
        step: Optional. The step size between the ngrams.
    """
    return zip(*(islice(it, i, step) for i, it in enumerate(tee(elements, ngram_length))))


def select_stay(days: Iterable[WebElement]) -> Union[None, Tuple[WebElement, WebElement]]:
    """Select the date of a 1-day stay.

    Args:
        days: Elements representing days.

    Returns:
        A tuple of 2 elements, the date of arrival and the
        date of departure. If there is no available time interval,
        the return value will be `None`.
    """
    day_attrib = "data-day"
    available_days = sorted(
        filter(_is_day_available, days),
        key=lambda x: int(x.get_attribute(day_attrib))
    )
    selected_days = None
    for bigram in get_ngrams(available_days, 2):
        left, rigth = bigram
        if int(left.get_attribute(day_attrib)) == int(rigth.get_attribute(day_attrib)) - 1:
            selected_days = bigram
            break
    return selected_days


def main() -> None:
    """Main function"""
    browser = configure_driver()
    browser.get("https://www.linsbergasia.at/websline-abm/homepage/booking/index/de")
    find_and_click(
        driver=browser,
        xpath_expr='//button[@class="btn btn-default btn-block dropdown-toggle"]'
    )
    find_and_click(
        driver=browser,
        xpath_expr='//a[@onclick="AjaxCalendarSet(2023, 4);return false;"]'
    )
    target_date = shift_date_by_months(6)
    days_xpath = make_xpath_for_days(year=target_date.year, month=target_date.month)
    days = select_elements(browser, days_xpath)
    stay = select_stay(days)
    print(stay)
    # browser.execute_script("arguments[0].click();", days[0])
    browser.quit()


if __name__ == "__main__":
    main()
