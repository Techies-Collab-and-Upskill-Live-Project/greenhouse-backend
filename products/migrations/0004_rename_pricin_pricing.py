# Generated by Django 5.1.2 on 2024-11-09 12:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_rename_pricing_pricin'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Pricin',
            new_name='Pricing',
        ),
    ]