# Generated by Django 5.1 on 2024-08-24 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_vendor_shop_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='shipping_zone',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
