# Generated by Django 5.1 on 2024-10-30 10:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_payment_reference'),
        ('products', '0003_alter_productimage_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='variation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.productvariation'),
        ),
    ]