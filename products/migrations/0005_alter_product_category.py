# Generated by Django 4.2.14 on 2024-09-29 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_product_status_alter_product_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(max_length=100),
        ),
    ]