from django.contrib import admin
from .models import *

# Register your models here.

TheModels  = [Cart, CartItem, Order, OrderItem]

admin.site.register(TheModels)
