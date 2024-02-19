from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from ...models import Stores

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

    @staticmethod
    def check(driver, checked):
        if not checked and driver.is_element_visible('div#px-captcha'):
            print('Bot check detected')
            actions = ActionChains(driver)
            element = driver.find_element('div#px-captcha')
            x = -(element.size['width'] / 2) + 50
            try:
                actions.move_to_element(element).move_by_offset(x,0).click_and_hold().pause(7).release().perform()
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
                    if len(Stores.objects.filter(ChainName='Walmart', StoreName=name, Location=location)) == 0:
                        print('Unique store, saving to db..')
                        store = Stores(ChainName='Walmart', StoreName=name, Location=location)
                        store.save()

            driver.quit()

        except Exception as e:
            print('something went wrong')
            driver.quit()
            if hasattr(e, 'msg'):
                print(e.msg)
            if hasattr(e, 'message'):
                print(e.message)
