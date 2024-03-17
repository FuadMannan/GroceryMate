import json

from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from myapp.forms import SignUpForm
from myapp.backend.nutrition.api import NutritionApi

from .backend.scrape_api import scrape_api
from .models import Stores, Products, Prices, GroceryLists, ListItems


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form, "page": "signup"})


@csrf_exempt
def scrape(request):
    store = request.GET.get('chain')
    if store in scrape_api.CHAIN_NAMES[1:]:
        scraper = scrape_api.LoblawsBrands(store)
    if request.path == '/scrape/get_locations':
            scraper.get_locations()
    elif request.path == '/scrape/get_products_prices':
            scraper.get_products_prices()
    items = {
        'store': store,
        'chains': scrape_api.CHAIN_NAMES,
        'store_items': Stores.objects.all(),
        'product_items': Products.objects.all(),
        'price_items': Prices.objects.all(),
    }
    return render(request, 'scrape.html', items)


def grocery_lists(request):
    grocery_lists = GroceryLists.objects.filter(UserID=request.user)

    return render(request, './grocery_lists.html', {
        "grocery_lists": grocery_lists,
    })


def save_grocery_lists(request):
    data = json.loads(request.body.decode('UTF-8'))

    grocery_list = GroceryLists.objects.create(
        UserID=request.user,
        ListName=data["name"]
    )

    return HttpResponse(json.dumps({'status': 200, 'id': grocery_list.ListID}), content_type="application/json")


def delete_grocery_list(request, id):
    GroceryLists.objects.filter(ListID=id).delete()

    return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


def edit_grocery_list(request, id):
    data = json.loads(request.body.decode('UTF-8'))

    GroceryLists.objects.filter(ListID=id).update(ListName=data["name"])

    return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


def grocery_items(request, id):
    items = ListItems.objects.filter(ListID=id)
    name = GroceryLists.objects.get(ListID=id).ListName

    return render(request, './grocery_items.html', {
        "grocery_list_items": items,
        "grocery_list_name": name
    })


def find_products(request):
    data = json.loads(request.body.decode('UTF-8'))

    results = {}

    prices = Prices.objects.filter(ProductID__ProductName__icontains=data['name'])

    for i, price in enumerate(prices):
        item = {}
        item['ProductName'] = price.ProductID.ProductName
        item['ChainName'] = price.ChainID.ChainName
        item['Price'] = str(price.Price)
        item['PriceID'] = price.pk
        results[f'{i}'] = item

    return HttpResponse(json.dumps({'status': 200, 'items': results}), content_type="application/json")


def add_grocery_list_item(request):
    data = json.loads(request.body.decode('UTF-8'))

    grocery_list = GroceryLists.objects.get(ListID=data['listID'])
    price = Prices.objects.get(PriceID=data['priceID'])

    listItem = ListItems.objects.create(
        ListID=grocery_list,
        PriceID=price
    )
    listItem.save()

    return HttpResponse(json.dumps({'status': 200, 'id': listItem.ItemID}), content_type="application/json")


def delete_grocery_list_item(request, id):
    ListItems.objects.filter(ItemID=id).delete()

    return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


def get_nutrition_info(request, name):
    data = NutritionApi().get_nutrition(name)

    return HttpResponse(json.dumps(data), content_type="application/json")
