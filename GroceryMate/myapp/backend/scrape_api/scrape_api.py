import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from seleniumbase import Driver
from abc import ABC, abstractmethod
import decimal
import time
import re
import json
import traceback

from ...models import Chains, Stores, Products, Prices
from django.db.utils import IntegrityError


CHAIN_NAMES = [
    'Walmart',
    'Loblaws',
    'No Frills',
    'Real Canadian Superstore',
    'Wholesale Club',
    'Valu-mart',
    'Fortinos',
    'Metro'
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


    def get_location_actions(self):
        return ((self.open_with_driver, self.locator_URL), self.loop_locations)


    def get_grocery_actions(self):
        return ((self.open_with_driver, self.grocery_URL), self.loop_grocery_items)


    def open_with_driver(self, url: str = None):
        if self.driver is None:
            self.driver = Driver(uc=True, headless=False)
        if url:
            self.driver.open(url)


    def update_page_soup(self):
        page_text = self.driver.get_page_source()
        self.soup = BeautifulSoup(page_text, 'html.parser')


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
            print(f'name: {name}\nlocation: {location}')
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
            print(f'Product: {name}')
            if not Products.objects.filter(ProductName=name).exists():
                product = Products(ProductName=name)
                product.save()
                print('New product saved')
            else:
                print('Existing product')
                product = Products.objects.get(ProductName=name)
            return product
        except IntegrityError as e:
            print(f'{e.__cause__}, skipping product')


    def save_price(self, product, price):
        try:
            print(f'Price: ${price}')
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
        self.attempt(self.get_location_actions())


    def get_products_prices(self):
        self.attempt(self.get_grocery_actions())


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
            error_message += f'{traceback.format_exc()}\n'
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


    def loop_locations(self):
        loaded = False
        while not loaded:
            time.sleep(1)
            self.update_page_soup()
            list_items = self.soup.select('li.location-list__item')
            if len(list_items) > 0:
                loaded = True
        for item in list_items:
            name = item.select_one('h2').text
            location = ', '.join([element.text for element in item.select('div.location-address__line')])
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


class Metro(Scraper):


    def __init__(self, load_cities_necessary=False) -> None:
        super().__init__(load_cities_necessary)
        self.chain = Chains.objects.get(ChainName='Metro')
        self.grocery_URL = 'https://www.metro.ca/en/'
        self.locator_URL = f'{self.grocery_URL}find-a-grocery'


    def get_location_actions(self):
        return (self.loop_locations,)


    def loop_locations(self):
        page = requests.post(self.locator_URL)
        self.soup = BeautifulSoup(page.content, 'html.parser')
        cities_var = self.soup.select('div#content-temp script')[2]
        cities_str = cities_var.text
        i1, i2 = cities_str.find('"{'), cities_str.find('}";') + 2
        cities_str = cities_str[i1:i2].encode().decode('unicode_escape').strip('"')
        cities_dict = json.loads(cities_str)
        for province in cities_dict:
            for city in cities_dict[province]:
                for i in range(3):
                    page = requests.post(self.locator_URL, data={'provinceCode': province, 'city': city})
                    if page.status_code == 200:
                        break
                    else:
                        time.sleep(70)
                soup = BeautifulSoup(page.content, 'html.parser')
                results = soup.select('div.white-wrapper')
                for result in results:
                    name = result.select_one('p.store-name').text
                    location = ", ".join([i.text.strip('\n') for i in result.select('div[class^="address--line"]')])
                    self.save_store(name, location)


    def loop_grocery_items(self):
        def get_aisle_url(aisle_name: str):
            return f'{self.grocery_URL}online-grocery/aisles/{aisle_name.lower().replace(" & ", "-").replace(" ", "-")}'
        self.update_page_soup()
        if len(self.soup.select('button#onetrust-reject-all-handler')) >= 1:
            self.driver.click('button#onetrust-reject-all-handler')
        if self.soup.select_one('html').attrs['lang'] == 'fr-CA':
            self.driver.click('.js-change-my-language')
        aisle_css = '.menu-toggle-nav.left-sidebar-sub--menu.aisles--menu.inactive>.nav--container>.sub--nav--first>ul>li'
        aisle_names = [i.text.strip() for i in self.soup.select(aisle_css)]
        aisle_links = [get_aisle_url(aisle_name) for aisle_name in aisle_names[:16]]
        for aisle in aisle_links:
            self.driver.open(aisle)
            more_pages = True
            while more_pages:
                self.update_page_soup()
                items = self.soup.select('.pt__content--wrap')
                for item in items:
                    product_name = item.select_one('.head__title').text
                    product = self.save_product(product_name)
                    product_price = item.select('.price-update')
                    if len(product_price) == 1:
                        product_price = product_price[0].text.strip('$')
                    else:
                        product_price = re.findall('\d+\.?\d+', item.select_one('.pricing__secondary-price span').text)[0]
                    product_price = decimal.Decimal(product_price)
                    self.save_price(product, product_price)
                more_pages = self.navigate_next('a[aria-label="Next"]')
