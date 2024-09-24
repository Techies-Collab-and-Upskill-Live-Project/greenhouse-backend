# Generated by Django 4.2.14 on 2024-09-20 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('Customer', 'Customer'), ('Vendor', 'Vendor')], default='Customer', max_length=50),
        ),
    ]