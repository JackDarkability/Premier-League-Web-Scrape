""" Module that holds all of the functions that scrape data from the website

setup_driver: Creates a driver for web scraping with the arguments wanted, for consistency

get_full_link: Creates the full link of a webpage to then be scraped 
based from its base URL and the details of the season

load_entire_page: Scrolls down the page to load all matches on a premier league site
by identifying that the loader is no longer there and pressing page down until that happens.
"""

import time
import logging

# The libraries needed for web scraping
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


def setup_driver():
    """Set up the web driver"""

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    return driver


def get_full_link(base_url, season, club="-1"):
    """Create full URL from the the details given along with a base URL
    which is contiguous for all URLs to scrape
    """

    full_url = f"{base_url}{season['competition']}&se={season['number']}&cl={club}"
    logging.debug(full_url)
    return full_url


def load_entire_page(driver):
    """Scroll down the page to load all matches"""

    html = driver.find_element(By.TAG_NAME, "html")
    html.send_keys(Keys.PAGE_DOWN)
    time.sleep(10)

    # Scroll down page until all matches are loaded
    while True:
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # If loader present then matches have not finished loading
        loader = soup.findAll(
            lambda tag: tag.name == "div"
            and "loader" in tag.get("class", [])
            and "u-hide" not in tag.get("class", [])
        )
        if not loader:
            logging.debug("No loader")
            break

    return soup

def initialise_dictionary(match):
    """
    """

    stats = ["possession_%", "shots_on_target", "shots", "touches", "passes","tackles", "clearances", "corners", "offsides", "yellow_cards", "red_cards", "fouls_conceded"]

    for stat in stats:
        match[stat + "_home"] = 0
        match[stat + "_away"] = 0
    
    return match

