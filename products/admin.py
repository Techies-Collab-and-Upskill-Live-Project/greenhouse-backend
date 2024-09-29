from django.contrib import admin
from .models import *
# Register your models here.
TheModels = [Category, Product, ProductImage, ProductSpecification, Pricing, ProductVariation]


admin.site.register(TheModels)