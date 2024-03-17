from celery import shared_task
from myapp.backend.scrape_api import scrape_api as scrape

@shared_task(bind=True)
def scrape_task(self):
    print('in celery')
    for i, chain in enumerate(scrape.CHAIN_NAMES[1:]):
        if i <= 5:
            scraper = scrape.LoblawsBrands(chain)
        else:
            scraper = scrape.Metro()
        scraper.get_locations()
        scraper.get_products_prices()
