from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import Driver
from abc import ABC, abstractmethod
import threading
import decimal

from ...models import Chains, Stores, Products, Prices

STORES = [
    'Walmart',
    'Loblaws'
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
                        # stores = Stores.objects.filter(ChainName='Walmart')
                        # for store in stores:
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
