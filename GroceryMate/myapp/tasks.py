from celery import shared_task
from myapp.backend.scrape_api import scrape_api as scrape

@shared_task(bind=True)
def scrape_task(self):
    print('in celery')
    scrape.Locations.get_Walmart()
    scrape.Locations.get_Loblaws_brands('Loblaws')
    scrape.Locations.get_Loblaws_brands('No Frills')
    scrape.ProductPrices.get_Walmart()
    scrape.ProductPrices.get_Loblaws_brands('Loblaws')
    scrape.ProductPrices.get_Loblaws_brands('No Frills')
