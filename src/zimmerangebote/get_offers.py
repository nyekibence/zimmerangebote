#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import expanduser
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def configure_driver() -> webdriver.Chrome:
    """Configure the Chrome driver for selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    homedir = expanduser("~")
    webdriver_service = Service(f"{homedir}/chromedriver/stable/chromedriver")
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.maximize_window()
    return driver


def find_and_click(driver: webdriver.Chrome, xpath_expr: str) -> webdriver.Chrome:
    """Find an element and click on it.

    Args:
        driver: The currently used Chrome driver.
        xpath_expr: An XPATH expression to identify the element.

    Returns:
         The Chrome driver after clicking on the element.
    """
    element = driver.find_element(By.XPATH, xpath_expr)
    element.click()
    return driver


def main() -> None:
    """Main function"""
    browser = configure_driver()
    browser.get("https://www.linsbergasia.at/websline-abm/homepage/booking/index/de")
    browser = find_and_click(
        driver=browser,
        xpath_expr='//button[@class="btn btn-default btn-block dropdown-toggle"]'
    )
    browser = find_and_click(
        driver=browser,
        xpath_expr='//a[@onclick="AjaxCalendarSet(2023, 4);return false;"]'
    )
    sleep(4)
    content = browser.page_source
    print(content)
    browser.quit()


if __name__ == "__main__":
    main()
