import json

from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from myapp.forms import SignUpForm

from .backend.scrape_api import scrape_api
from .models import Chains, Stores, Products, Prices, GroceryLists


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
    if request.method == 'GET':
        items = {
            'stores': scrape_api.STORES,
            'store_items': Stores.objects.all(),
            'product_items': Products.objects.all(),
            'price_items': Prices.objects.all(),
        }
        return render(request, 'scrape.html', items)


@csrf_exempt
def scrape(request):
    store = request.GET.get('chain')
    if request.path == '/scrape/get_locations':
        if store == 'Walmart':
            scrape_api.Locations.get_Walmart()
        elif store == 'Loblaws':
            scrape_api.Locations.get_Loblaws()
    elif request.path == '/scrape/get_products_prices':
        scrape_api.ProductPrices.get_Walmart()
    items = {
        'store': request.GET.get('chain'),
        'stores': scrape_api.STORES,
        'store_items': Stores.objects.all(),
        'chain_items': Chains.objects.all(),
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

    GroceryLists.objects.create(
        UserID=request.user,
        ListName=data["name"]
    )

    return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


def delete_grocery_list(request, id):
    GroceryLists.objects.filter(ListID=id).delete()

    return HttpResponse(json.dumps({'status': 200}), content_type="application/json")


def edit_grocery_list(request, id):
    data = json.loads(request.body.decode('UTF-8'))

    GroceryLists.objects.filter(ListID=id).update(ListName=data["name"])

    return HttpResponse(json.dumps({'status': 200}), content_type="application/json")
