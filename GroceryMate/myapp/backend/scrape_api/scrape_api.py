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


class Scraper(ABC):


    def __init__(self, load_cities_necessary=False) -> None:
        super().__init__()
        self.chain = None
        self.load_cities_necessary = load_cities_necessary
        self.locator_URL = None
        self.grocery_URL = None
        self.driver = None
        self.soup = None
        self.location_actions = ((self.open_with_driver, self.locator_URL), self.load_locator, self.loop_locations)
        self.grocery_actions = ((self.open_with_driver, self.grocery_URL), self.loop_grocery_items)


    def open_with_driver(self, url: str = None):
        if self.driver is None:
            self.driver = Driver(uc=True, headless=False)
        if url:
            self.driver.open(url)


    def update_page_soup(self):
        page_text = self.driver.get_page_source()
        self.soup = BeautifulSoup(page_text, 'html.parser')


    @staticmethod
    def print_city(name, location):
        print(f"name: {name}\nlocation: {location}")


    def load_locator(self):
        pass


    @abstractmethod
    def loop_locations(self):
        pass


    @abstractmethod
    def loop_grocery_items(self):
        pass


    def save_store(self, name, location):
        try:
            criteria = {'ChainID': self.chain, 'StoreName': name, 'Location': location}
            if not Stores.objects.filter(**criteria).exists():
                store = Stores(**criteria)
                store.save()
                print('New store saved\n')
            else:
                print('Existing store\n')
        except IntegrityError as e:
            print(f'{e.__cause__}, skipping store\n')


    def save_product(self, name):
        try:
            if not Products.objects.filter(ProductName=name).exists():
                product = Products(ProductName=name)
                product.save()
                print('New product saved\n')
            else:
                print('Existing product\n')
                product = Products.objects.get(ProductName=name)
            return product
        except IntegrityError as e:
            print(f'{e.__cause__}, skipping product\n')


    def save_price(self, product, price):
        try:
            criteria = {'ChainID': self.chain, 'ProductID': product}
            if not Prices.objects.filter(**criteria).exists():
                new_price = Prices(**criteria, Price=price)
                new_price.save()
                print('New price saved\n')
            elif Prices.objects.get(**criteria).Price != price:
                current_price = Prices.objects.get(**criteria)
                criteria['PriceID'] = current_price.pk
                price_update = {'Price': price}
                Prices.objects.filter(**criteria).update(**price_update)
                print('Price updated\n')
            else:
                print('Same price\n')
        except IntegrityError as e:
            print(f'{e.__cause__}, skipping price\n')


    def navigate_next(self, next_button_css, stop='disabled'):
        next_button = self.soup.select_one(next_button_css)
        if next_button and not stop in next_button.attrs:
            self.driver.click(next_button_css)
            return True
        else:
            return False


    def get_locations(self):
        self.attempt(self.location_actions)

    def get_products_prices(self):
        self.attempt(self.grocery_actions)

    def attempt(self, actions):
        try:
            for action in actions:
                if type(action) is tuple:
                    arg = action[1]
                    action[0](arg)
                else:
                    action()
        except (StaleElementReferenceException, Exception) as e:
            error_message = f'Encountered {type(e)} at {self.driver.current_url}:\n'
            if hasattr(e, 'msg'):
                error_message += f'msg: {e.msg}\n'
            if hasattr(e, 'message'):
                error_message += f'message: {e.message}\n'
            error_message += f'Cause: {e.__cause__}\n'
            if hasattr(e, 'stacktrace'):
                error_message += f'Stacktrace: {e.stacktrace}\n'
            error_message += f'{e}\n'
            print(error_message)
        else:
            print('Actions completed, exiting browser')
        finally:
            if self.driver:
                self.driver.quit()


class LoblawsBrands(Scraper):


    def __init__(self, brand, load_cities_necessary=False) -> None:
        super().__init__(load_cities_necessary)
        self.brand = brand
        self.chain = Chains.objects.get(ChainName=self.brand)
        self.grocery_URL = f"https://www.{brand.lower().replace(' ', '').replace('-', '')}.ca"
        self.locator_URL = f"{self.grocery_URL}/store-locator"
        self.location_actions = ((self.open_with_driver, self.locator_URL), self.loop_locations)


    def loop_locations(self):
        loaded = False
        while not loaded:
            time.sleep(1)
            self.update_page_soup
            list_items = self.soup.select('li.location-list__item')
            if len(list_items) > 0:
                loaded = True
        for item in list_items:
            name = item.select_one('h2').text
            location = ', '.join([element.text for element in item.select('div.location-address__line')])
            self.print_city(name, location)
            self.save_store(name, location)


    def loop_grocery_items(self):
        def full_link(href):
            return f'{self.grocery_URL}{href}'
        def wait_until_loaded(main=False):
            is_loaded = False
            start = time.time()
            while not is_loaded:
                time.sleep(1)
                if time.time() - start > 15:
                    self.driver.refresh()
                    start = time.time()
                self.update_page_soup()
                if main:
                    is_loaded = len(self.soup.select('ul[data-code="root"]')) > 0
                else:
                    is_loaded = len(self.soup.select('h1')) > 0
        wait_until_loaded(main=True)
        if self.driver.find_element('button.lds__privacy-policy__btnClose'):
            self.driver.click('button.lds__privacy-policy__btnClose')
        category_list_items = self.soup.select('ul[data-code="xp-455-food-departments"] > li')
        categories = [full_link(item.select_one('a').attrs['href']) for item in category_list_items]
        for category in categories:
            self.driver.open(category)
            wait_until_loaded()
            subcategories = [full_link(link.attrs['href']) for link in self.soup.select('a[data-testid="header-link"]')]
            for subcategory in subcategories:
                self.driver.open(subcategory)
                wait_until_loaded()
                more_pages = True
                while more_pages:
                    wait_until_loaded()
                    items = self.soup.select('div.chakra-linkbox')
                    for item in items:
                        product_name = item.select_one('h3[data-testid="product-title"]').text.replace('  ', ' ').strip()
                        product = self.save_product(product_name)
                        data_testid_prices = item.select('[data-testid$="price"]')
                        product_price = None
                        for data_testid_price in data_testid_prices:
                            if data_testid_price.attrs['data-testid'] in ('regular-price', 'non-members-price', 'sale-price'):
                                product_price = re.sub(r'[^\d\.]', '', data_testid_price.select_one('.css-idkz9h').text)
                        if not product_price:
                            continue
                        product_price = decimal.Decimal(product_price)
                        self.save_price(product, product_price)
                    more_pages = self.navigate_next('button[aria-label="Next Page"]')
