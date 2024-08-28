from django.db import models
from django.utils.crypto import get_random_string
import uuid
from users.models import Vendor

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=6, unique=True, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    color = models.CharField(max_length=100)
    description = models.TextField()
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_random_string(length=6, allowed_chars='0123456789')
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    
    def __str__(self):
        return f"{self.product.name} Image"

class ProductVariation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    seller_sku = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.product.name} Variation"

class ProductSpecification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='specification')
    certifications = models.CharField(max_length=255)
    model = models.CharField(max_length=100)
    material_family = models.CharField(max_length=100)
    size_length = models.PositiveIntegerField()
    size_width = models.PositiveIntegerField()
    size_height = models.PositiveIntegerField()
    warranty_duration = models.PositiveIntegerField()
    warranty_type = models.CharField(max_length=100)
    product_line = models.CharField(max_length=100)
    notes = models.TextField()
    
    def __str__(self):
        return f"{self.product.name} Specification"

class Pricing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='pricing')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sales_start_date = models.DateField()
    sales_end_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name} Pricing"


