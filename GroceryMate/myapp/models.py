from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError


# Create your models here.
class BaseModel(models.Model):

    class Meta:
        abstract = True

    def validate_empty(self):
        charFields = [field for field in self._meta.fields if type(field) == models.fields.CharField]
        for field in charFields:
            blank = field.__dict__['blank']
            fieldName = field.__dict__['name']
            value: str = getattr(self, fieldName)
            if blank == False and not value.strip():
                raise ValidationError(f'{fieldName} cannot be blank')

    def clean(self) -> None:
        self.validate_empty()
        return super().clean()

    def save(self, *args, **kwargs) -> None:
        self.clean()
        return super().save(*args, **kwargs)


class Brands(BaseModel):
    BrandID = models.BigAutoField(primary_key=True, verbose_name='Brand ID')
    BrandName = models.CharField(max_length=255)


class Products(BaseModel):
    ProductID = models.BigAutoField(primary_key=True, verbose_name='Product ID')
    ProductName = models.CharField(max_length=255)
    BrandID = models.ForeignKey(Brands, on_delete=models.CASCADE)
    Category = models.CharField(max_length=255, default='None')


class Chains(BaseModel):
    ChainID = models.SmallAutoField(primary_key=True, verbose_name='Chain ID')
    ChainName = models.CharField(max_length=255)


class Stores(BaseModel):
    StoreID = models.BigAutoField(primary_key=True, verbose_name='Store ID')
    ChainID = models.ForeignKey(Chains, on_delete=models.CASCADE)
    StoreName = models.CharField(max_length=255)
    Location = models.CharField(max_length=255, unique=True)


class Prices(BaseModel):
    PriceID = models.BigAutoField(primary_key=True, verbose_name='Price ID')
    ProductID = models.ForeignKey(Products, on_delete=models.CASCADE)
    ChainID = models.ForeignKey(Chains, on_delete=models.CASCADE)
    Price = models.DecimalField(max_digits=5, decimal_places=2, null=False)


class NutritionalInfo(BaseModel):
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


class GroceryLists(BaseModel):
    ListID = models.BigAutoField(primary_key=True, verbose_name='List ID')
    UserID = models.ForeignKey(User, on_delete=models.CASCADE)
    ListName = models.CharField(max_length=255)
    DateCreated = models.DateField(auto_now_add=True)


class ListItems(BaseModel):
    ItemID = models.BigAutoField(primary_key=True, verbose_name='List Item ID')
    ListID = models.ForeignKey(GroceryLists, on_delete=models.CASCADE)
    PriceID = models.ForeignKey(Prices, on_delete=models.CASCADE)
    Quantity = models.SmallIntegerField(default=1)
    Unit = models.CharField(max_length=10, blank=True)
    IsChecked = models.BooleanField(default=False)
