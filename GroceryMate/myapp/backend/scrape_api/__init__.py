from myapp.models import Chains, Brands
from .scrape_api import CHAIN_NAMES

# Initialize chains
if Chains.objects.count() != len(CHAIN_NAMES):
    for name in CHAIN_NAMES:
        if not Chains.objects.filter(ChainName=name).exists():
            new_chain = Chains(ChainName=name)
            new_chain.save()

# Initialize 'None' brand
if Brands.objects.count() == 0:
    brand = Brands(BrandName='None')
    brand.save()
