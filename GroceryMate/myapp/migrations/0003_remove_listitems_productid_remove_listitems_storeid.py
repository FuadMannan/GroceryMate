# Generated by Django 4.2.9 on 2024-03-02 23:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_chains_remove_prices_storeid_remove_stores_chainname_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listitems',
            name='ProductID',
        ),
        migrations.RemoveField(
            model_name='listitems',
            name='StoreID',
        ),
    ]
