from myapp.models import Chains
from .scrape_api import CHAIN_NAMES

if Chains.objects.count() != len(CHAIN_NAMES):
    for name in CHAIN_NAMES:
        if not Chains.objects.filter(ChainName=name).exists():
            new_chain = Chains(ChainName=name)
            new_chain.save()