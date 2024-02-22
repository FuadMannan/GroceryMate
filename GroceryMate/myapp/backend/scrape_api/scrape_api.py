from bs4 import BeautifulSoup
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import Driver

from ...models import Chains, Stores

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
    def check(driver, checked):
        if not checked and driver.is_element_visible('div#px-captcha'):
            print('Bot check detected')
            actions = ActionChains(driver)
            element = driver.find_element('div#px-captcha')
            x = -(element.size['width'] / 2) + 50
            try:
                actions.move_to_element(element).move_by_offset(x, 0).click_and_hold().pause(7).release().perform()
                print('action performed')
                checked = True
            except StaleElementReferenceException as e:
                if hasattr(e, 'msg'):
                    print(e.msg)

    @staticmethod
    def get_Walmart():

        if Locations.cities is None:
            print('Initializing cities')
            Locations.init()

        URL = 'https://www.walmart.ca/en/stores-near-me'

        checked = False

        try:
            driver = open_with_driver(URL)
            driver.sleep(3)

            # Filter for locations with groceries
            driver.click('div.hidden-xs > div.sfa-filter__summary > div > button.sfa-wm-btn--secondary')
            driver.click('label[title="Grocery"] > div.sfa-filter__checkbox__checkmark__wrapper')
            driver.click('button.sfa-wm-btn.sfa-filter__apply__button')
            driver.sleep(2)
            driver.refresh()
            driver.sleep(2)
            Locations.check(driver, checked)

            chain = Chains.objects.get(ChainName='Walmart')

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
