from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
import csv
from time import perf_counter
import config

city_from = input("What is the city of departure: ")
city_to = input("What is the city of destination: ")
day_count = int(input("How many days in advance: "))

connection_for_day = []


def format_date(date_string):
    month_names = {
        'sty': 1, 'lut': 2, 'mar': 3, 'kwi': 4,
        'maj': 5, 'cze': 6, 'lip': 7, 'sie': 8,
        'wrz': 9, 'paź': 10, 'lis': 11, 'gru': 12
    }
    parts = date_string.split(', ')
    day, month_str = parts[1].split(' ')
    month = month_names.get(month_str.lower())
    date = datetime(datetime.now().year, month, int(day))
    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date


def init_driver(link_to_scrape, days_in_advance):
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_driver_path = config.chrome_driver_path
    driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 3)
    driver.get(link_to_scrape)
    driver.maximize_window()
    shadow_host = driver.find_element(By.ID, 'usercentrics-root')
    time.sleep(1)
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
    time.sleep(1)
    accept_button = shadow_root.find_element(By.CSS_SELECTOR, 'button[data-testid="uc-accept-all-button"]')
    accept_button.click()
    city_of_departure = wait.until(EC.element_to_be_clickable((By.ID, 'searchInput-from')))
    city_of_departure.send_keys(city_from)
    time.sleep(1)
    city_of_departure.send_keys(Keys.ARROW_DOWN)
    time.sleep(1)
    city_of_departure.send_keys(Keys.ENTER)
    time.sleep(1)
    city_of_destination = wait.until(EC.element_to_be_clickable((By.ID, 'searchInput-to')))
    city_of_destination.send_keys(city_to)
    time.sleep(1)
    city_of_destination.send_keys(Keys.ARROW_DOWN)
    time.sleep(1)
    city_of_destination.send_keys(Keys.ENTER)
    search_routes_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Wyszukaj trasy"]')
    search_routes_button.click()

    start = perf_counter()
    while days_in_advance >= 0:
        time.sleep(3)
        try:
            earlier_trips_button = driver.find_element(By.CSS_SELECTOR,
                                                       'button[data-e2e="collapsed-trips-toggle-early"]')
            earlier_trips_button.click()
        except NoSuchElementException:
            pass
        try:
            later_trips_button = driver.find_element(By.CSS_SELECTOR, 'button[data-e2e="collapsed-trips-toggle-late"]')
            later_trips_button.click()
        except NoSuchElementException:
            pass

        result_route_for_day = driver.find_elements(By.XPATH, '//li[contains(@data-e2e, "search-result-item")]')
        departure_date = driver.find_element(By.ID, 'dateInput-from').get_attribute('value')
        departure_date = format_date(departure_date)

        for route in result_route_for_day:
            departure_station = route.find_element(By.CSS_SELECTOR,
                                                   'div[data-e2e="search-result-departure-station"]').text
            arrival_station = route.find_element(By.CSS_SELECTOR,
                                                 'div[data-e2e="search-result-arrival-station"]').text
            departure_time = route.find_element(By.CSS_SELECTOR,
                                                'div[data-e2e="search-result-departure-time"]').text.split("\n")[0]
            arrival_time = route.find_element(By.CSS_SELECTOR,
                                              'div[data-e2e="search-result-arrival-time"]').text.split("\n")[0]
            duration_time = route.find_element(By.CSS_SELECTOR,
                                               'span[data-e2e="search-result-duration"]').text.split(" ")[0]
            price_with_currency = route.find_element(By.CSS_SELECTOR,
                                                     'span[data-e2e="search-result-prices"]').text
            try:
                price = price_with_currency.split(" ")[0]
            except IndexError:
                price = None
            try:
                currency = price_with_currency.split(" ")[1]
            except IndexError:
                currency = None

            connections = {
                "cityFrom": departure_station,
                "cityTo": arrival_station,
                "date": departure_date,
                "timeOfDeparture": departure_time,
                "timeOfArrival": arrival_time,
                "travelTime": duration_time,
                "price": price,
                "currency": currency
            }

            connection_for_day.append(connections)

        next_day_button = driver.find_elements(By.CSS_SELECTOR, 'a[data-e2e="date-picker-item"]')[2]
        next_day_button.click()
        days_in_advance -= 1
    fields = ["cityFrom", "cityTo", "date", "timeOfDeparture", "timeOfArrival", "travelTime", "price", "currency"]
    found_connections = f"connections_flixbus_{city_from}_{city_to}.csv"
    with open(found_connections, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(connection_for_day)

    end = perf_counter()
    print(f"Elapsed time = {start}, {end}")
    driver.quit()


init_driver("https://www.flixbus.pl/", day_count)
