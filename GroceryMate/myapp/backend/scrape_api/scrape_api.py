from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from seleniumbase import Driver
from abc import ABC, abstractmethod
import decimal
import time
import re

from ...models import Chains, Stores, Products, Prices
from django.db.utils import IntegrityError

STORES = [
    'Walmart',
    'Loblaws',
    'No Frills',
]


def open_with_driver(url):
    driver = Driver(uc=True, headless=True)
    driver.open(url)
    return driver


def page_soup(driver: Driver):
    page_text = driver.get_page_source()
    soup = BeautifulSoup(page_text, 'html.parser')
    return soup


class Locations:


    @staticmethod
    def get_Loblaws_brands(brand):


        URL = f"https://www.{brand.lower().replace(' ', '')}.ca/store-locator"

        try:

            driver = open_with_driver(URL)

            loaded = False
            while not loaded:
                time.sleep(1)
                soup = page_soup(driver)
                list_items = soup.select('li.location-list__item')
                if len(list_items) > 0:
                    loaded = True

            chain = Chains.objects.get(ChainName=brand)

            for item in list_items:

                name = item.select_one('h2').text

                location = ', '.join([element.text for element in item.select('div.location-address__line')])

                print(f"{name}\n{location}\n\n")

                try:

                    if not Stores.objects.filter(StoreName=name, Location=location).exists():

                        store = Stores(ChainID=chain, StoreName=name, Location=location)
                        store.save()

                except IntegrityError as e:
                    print(f'{e.__cause__}. Skipping last store.\n\n')

            driver.quit()

        except Exception as e:
            error_message = f'Encountered an issue at {driver.current_url}:\n{(type(e))}: '
            if hasattr(e, 'msg'):
                error_message += e.msg
            elif hasattr(e, 'message'):
                error_message += e.message
            else:
                error_message += 'No message provided'
            print(error_message)
        finally:
            driver.quit()

class ProductPrices():


    @staticmethod
    def get_Loblaws_brands(brand):

        URL = f"https://www.{brand.lower().replace(' ', '')}.ca"

        def full_link(href):
            return f'{URL}{href}'

        def wait_until_loaded(driver, main=False):
            is_loaded = False
            start = time.time()

            # Wait while not loaded
            while not is_loaded:
                time.sleep(1)
                soup = page_soup(driver)

                # If waiting for main page to load
                if main:
                    is_loaded = len(soup.select('ul[data-code="root"]')) > 0

                # If waiting on other pages
                else:
                    is_loaded = len(soup.select('h1')) > 0

                # If page (probably) stopped loading
                if time.time() - start > 15:
                    start = time.time()
                    driver.refresh()

            return soup

        try:

            driver = open_with_driver(URL)

            soup = wait_until_loaded(driver, True)
            cat_li = soup.select('ul[data-code="xp-455-food-departments"] > li')

            # Category links
            categories = [full_link(item.select_one('a').attrs['href']) for item in cat_li]

            chain = Chains.objects.get(ChainName=brand)

            # Cycle through categories
            for category in categories:
                driver.open(category)

                # Wait until page is loaded
                soup = wait_until_loaded(driver)

                # Get subcategories for category
                subcategories = [full_link(link.attrs['href']) for link in
                                 soup.select('a[data-testid="header-link"]')]

                # Cycle through subcategories
                for subcategory in subcategories:
                    driver.open(subcategory)

                    # Wait until page is loaded
                    soup = wait_until_loaded(driver)
                    items = soup.select('div.chakra-linkbox')

                    # Cycle through items on page
                    for item in items:
                        # Get product name
                        name = item.select_one(
                            'h3[data-testid="product-title"]'
                            ).text.replace('  ', ' ').strip()

                        # Get product price
                        data_testid_prices = item.select('[data-testid$="price"]')
                        item_price = None
                        for data_testid_price in data_testid_prices:
                            if data_testid_price.attrs['data-testid'] in (
                                'regular-price', 'non-members-price', 'sale-price'
                            ):
                                item_price = re.sub(r'[^\d\.]', '',
                                                    data_testid_price.select_one('.css-idkz9h').text)
                        item_price = decimal.Decimal(item_price)

                        if not item_price:
                            continue

                        # Save new product
                        if not Products.objects.filter(ProductName=name).exists():
                            product = Products(ProductName=name)
                            product.save()
                            print('New product saved')

                        # Get existing product
                        else:
                            product = Products.objects.get(ProductName=name)
                            print('Existing product')

                        criteria = {'ProductID': product, 'ChainID': chain}

                        # Save new price
                        if not Prices.objects.filter(**criteria).exists():
                            new_price = Prices(Price=item_price, **criteria)
                            new_price.save()
                            print('New price saved\n')

                        # Update existing price
                        elif Prices.objects.get(**criteria).Price != item_price:
                            current_price = Prices.objects.get(**criteria)
                            criteria['PriceID'] = current_price.pk
                            price_update = {'Price': item_price}
                            Prices.objects.filter(**criteria).update(**price_update)
                            print('Price updated\n')

                        # Same price, continue loop
                        else:
                            print('Same price\n')

            driver.quit()

        except Exception as e:
            error_message = f'Encountered an issue at {driver.current_url}:\n{(type(e))}: '
            if hasattr(e, 'msg'):
                error_message += e.msg
            elif hasattr(e, 'message'):
                error_message += e.message
            else:
                error_message += str(e)
            print(error_message)

        finally:
            driver.quit()
