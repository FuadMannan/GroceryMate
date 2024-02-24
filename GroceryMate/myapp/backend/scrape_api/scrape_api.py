from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import Driver
from abc import ABC, abstractmethod
import threading
import decimal
import time

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


class check(threading.Thread, ABC):

    def __init__(self, driver: Driver, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.driver = driver
        self.checked = False
        self.is_checking = False
        self.sleeptime = 10

    @abstractmethod
    def run(self) -> None:
        pass


class walmart_check(check):

    def __init__(self, driver: Driver) -> None:
        super().__init__(driver)

    def run(self):
        while not self.checked and self.driver.is_element_visible('div#px-captcha'):
            self.is_checking = True
            print('Bot check detected')
            actions = ActionChains(self.driver)
            element = self.driver.find_element('div#px-captcha')
            x = -(element.size['width'] / 2) + 50
            try:
                actions.move_to_element(element).move_by_offset(x,0)
                actions.click_and_hold().pause(self.sleeptime).release().perform()
            except (StaleElementReferenceException, Exception) as e:
                error_message = f'Encountered an issue at {self.driver.current_url}:\n{(type(e))}: '
                if hasattr(e, 'msg'):
                    error_message += e.msg
                elif hasattr(e, 'message'):
                    error_message += e.message
                else:
                    error_message += 'No message provided'
                print(error_message)

        self.is_checking = False
        self.checked = True


class Locations:

    cities = None

    @staticmethod
    def init():
        f = open('cities.txt')
        Locations.cities = f.read().split('\n')
        f.close()
        chains = Chains.objects.all().values()
        if len(chains) != len(STORES):
            for store in STORES:
                if chains.filter(ChainName=store):
                    continue
                chain = Chains(ChainName=store)
                chain.save()

    @staticmethod
    def get_Walmart():

        if Locations.cities is None:
            print('Initializing cities')
            Locations.init()

        URL = 'https://www.walmart.ca/en/stores-near-me'

        try:
            driver = open_with_driver(URL)
            bot_check = walmart_check(driver)
            bot_check.start()
            driver.sleep(3)

            # Filter for locations with groceries
            driver.click('div.hidden-xs > div.sfa-filter__summary > div > button.sfa-wm-btn--secondary')
            driver.click('label[title="Grocery"] > div.sfa-filter__checkbox__checkmark__wrapper')
            driver.click('button.sfa-wm-btn.sfa-filter__apply__button')
            driver.sleep(2)
            driver.refresh()
            driver.sleep(2)

            chain = Chains.objects.get(ChainName='Walmart')

            if bot_check.is_checking:
                driver.sleep(bot_check.sleeptime + 2)

            # Search for locations by city
            for city in Locations.cities:
                print(city)

                # Enter city name in search
                driver.type('input[tabindex="0"]', f"{city}, Canada\n")
                driver.sleep(2)
                storeSoup = page_soup(driver)

                # Get search results as BeautifulSoup resultset
                storeList = storeSoup.select('div[id^="sfa-store-list-item"]')

                # Iterate through search results
                for item in storeList:

                    # Click on search result
                    driver.click(f"div#{item.attrs['id']}")

                    # Get store name and location info
                    storeSoup = page_soup(driver)
                    name = storeSoup.select_one('a.automation-store-details-link').text
                    location = storeSoup.select_one('div.info-content.address > div').text
                    print(f"name: {name}\nlocation: {location}\n\n")

                    # Add store if doesn't exist in database
                    if len(Stores.objects.filter(StoreName=name, Location=location)) == 0:
                        print('Unique store, saving to db..')
                        store = Stores(ChainID=chain, StoreName=name, Location=location)
                        store.save()
            bot_check.checked = True

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
            driver.quit()

    def get_Loblaws_brands(brand):

        if Locations.cities is None:
            print('Initializing cities')
            Locations.init()

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

    def get_Walmart():

        URL = 'https://www.walmart.ca/en/cp/grocery/10019'

        try:

            driver = open_with_driver(URL)

            bot_check = walmart_check(driver)
            bot_check.start()

            # Close privacy toast
            if driver.is_element_visible('[aria-label="close button"]'):
                driver.js_click('[aria-label="close button"]')
                driver.js_click('[aria-label="Close Select the grocery link to find all grocery items."]')

            soup = page_soup(driver)

            # Get list of grocery categories
            categories = [link.attrs['href'] for link in
                        soup.select('div#Hubspokes4orNxMGrid > div > a[href*="/cp/grocery/"]')]

            chain = Chains.objects.get(ChainName='Walmart')

            # Iterate through categories
            for category in categories:
                driver.open(category)

                soup = page_soup(driver)

                # Click "Shop All" link, does not necessarily contain *all* products in category
                # TODO: get all products in category
                shop_all_link = soup.select_one('a[href*="shop_all"]')
                if shop_all_link is not None:
                    driver.open(shop_all_link.attrs['href'])
                else:
                    continue

                # Get items from page
                soup = page_soup(driver)
                items = soup.select('div[data-item-id]')

                for item in items:

                    # Get product name
                    name = item.select_one('span[data-automation-id="product-title"]').text

                    # Save new products
                    if len(Products.objects.filter(ProductName=name)) == 0:
                        print('Unique product, saving to db..')
                        product = Products(ProductName=name)
                        product.save()

                    # Get existing product
                    else:
                        product = Products.objects.get(ProductName=name)

                    # Get price
                    price = item.select_one('div[data-automation-id="product-price"] > div').text

                    # Strip "$" from price if in dollars
                    if '$' in price:
                        price = decimal.Decimal(price[1:])

                    # Convert cents to dollar value
                    else:
                        price = decimal.Decimal(f"{price[:-1]}.00") / 100

                    # Save price for stores

                    # Update existing price records
                    current_price = Prices.objects.filter(ProductID=product.pk, ChainID=chain.pk)
                    if len(current_price) > 0 :
                        if current_price[0].Price != price:
                            criteria = {'PriceID' : current_price[0].pk, 'ProductID' : product.pk, 'ChainID' : chain.pk}
                            price_update = {'Price' : price}
                            count = Prices.objects.filter(**criteria).update(**price_update)
                            print(f"{count} records updated")
                        else:
                            continue

                    # Add new price records
                    else:
                        new_price = Prices(ProductID=product, ChainID=chain, Price=price)
                        new_price.save()

        except Exception as e:
            error_message = f'Encountered an issue at {driver.current_url}:\n{(type(e))}: '
            if hasattr(e, 'msg'):
                error_message += e.msg
            elif hasattr(e, 'message'):
                error_message += e.message
            else:
                error_message += 'No message provided'
            print(error_message)
            bot_check.checked = True
            driver.quit()

        bot_check.checked = True
        driver.quit()

    def get_Loblaws():

        URL = 'https://www.loblaws.ca'

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
                if time.time() - start > 10:
                    driver.refresh()

            return soup

        try:

            driver = open_with_driver(URL)

            soup = wait_until_loaded(driver, True)
            cat_li = soup.select('ul[data-code="xp-455-food-departments"] > li')

            # Category links
            categories = [full_link(item.select_one('a').attrs['href']) for item in cat_li]

            chain = Chains.objects.get(ChainName='Loblaws')

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
                        price = item.select_one(
                            'p[data-testid="price"]'
                            ).text.replace('about', '').replace('sale', '').strip()[1:]
                        price = decimal.Decimal(price)

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
                            new_price = Prices(Price=price, **criteria)
                            new_price.save()
                            print('New price saved\n')

                        # Update existing price
                        elif Prices.objects.get(**criteria).Price != price:
                            current_price = Prices.objects.get(**criteria)
                            criteria['PriceID'] = current_price.pk
                            price_update = {'Price': price}
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
