from django.contrib import admin

from .models import Products, Prices, Stores, NutritionalInfo, GroceryLists, ListItems

# Register your models here.
admin.site.register(Products)
admin.site.register(Prices)
admin.site.register(Stores)
admin.site.register(NutritionalInfo)
admin.site.register(GroceryLists)
admin.site.register(ListItems)
