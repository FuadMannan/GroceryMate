from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Products(models.Model):
    ProductID = models.BigAutoField(primary_key=True, verbose_name='Product ID')
    ProductName = models.CharField(max_length=255)
    Category = models.CharField(max_length=255, null=True)


class Stores(models.Model):
    StoreID = models.BigAutoField(primary_key=True, verbose_name='Store ID')
    ChainName = models.CharField(max_length=255)
    StoreName = models.CharField(max_length=255)
    Location = models.CharField(max_length=255, unique=True)


class Prices(models.Model):
    PriceID = models.BigAutoField(primary_key=True, verbose_name='Price ID')
    ProductID = models.ForeignKey(Products, on_delete=models.CASCADE)
    StoreID = models.ForeignKey(Stores, on_delete=models.CASCADE)
    Price = models.DecimalField(max_digits=5, decimal_places=2, null=False)


class NutritionalInfo(models.Model):
    NutritionID = models.BigAutoField(primary_key=True, verbose_name='Nutrition ID')
    ProductID = models.ForeignKey(Products, on_delete=models.CASCADE)
    Calories = models.DecimalField(max_digits=7, decimal_places=2)
    ServingSize = models.DecimalField(max_digits=7, decimal_places=2)
    FatTotal = models.DecimalField(max_digits=7, decimal_places=2)
    FatSaturated = models.DecimalField(max_digits=7, decimal_places=2)
    Protein = models.DecimalField(max_digits=7, decimal_places=2)
    Sodium = models.PositiveSmallIntegerField()
    Potassium = models.PositiveSmallIntegerField()
    Cholesterol = models.PositiveSmallIntegerField()
    Carbohydrates = models.DecimalField(max_digits=7, decimal_places=2)
    Fiber = models.DecimalField(max_digits=7, decimal_places=2)
    Sugar = models.DecimalField(max_digits=7, decimal_places=2)


class GroceryLists(models.Model):
    ListID = models.BigAutoField(primary_key=True, verbose_name='List ID')
    UserID = models.ForeignKey(User, on_delete=models.CASCADE)
    ListName = models.CharField(max_length=255)
    DateCreated = models.DateField(auto_now_add=True)


class ListItems(models.Model):
    ItemID = models.BigAutoField(primary_key=True, verbose_name='List Item ID')
    ListID = models.ForeignKey(GroceryLists, on_delete=models.CASCADE)
    ProductID = models.ForeignKey(Products, on_delete=models.CASCADE)
    PriceID = models.ForeignKey(Prices, on_delete=models.CASCADE)
    StoreID = models.ForeignKey(Stores, on_delete=models.CASCADE)
    Quantity = models.SmallIntegerField(null=True)
    Unit = models.CharField(max_length=10, null=True)
    IsChecked = models.BooleanField(default=False)
