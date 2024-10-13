from django.db import models
from django.utils.crypto import get_random_string
import uuid, random
from users.models import Vendor
from decimal import Decimal


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


# Function to generate category choices dynamically
def get_category_choices():
    return [(category.name,  category.name) for category in Category.objects.all()]

STATUS_CHOICE = (
    ('in stock', 'In Stock'),
    ('out of stock', 'Out of Stock'),
    ('inactive', 'Inactive'),
)

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=6, unique=True, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField( max_length=15, choices=STATUS_CHOICE, default='in stock')
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku:
            # Generate a 6-digit numeric SKU
            self.sku = self.generate_unique_sku()
        super().save(*args, **kwargs)

    def generate_unique_sku(self):
        while True:
            sku = f"{random.randint(100000, 999999)}"  # Generate a 6-digit number
            if not Product.objects.filter(sku=sku).exists():
                return sku

class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} Image"

class ProductVariation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    seller_sku = models.CharField(max_length=100, blank=True, null=True)
    barcode = models.CharField(max_length=100 , blank=True, null=True)
    quantity = models.PositiveIntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} Variation"

class ProductSpecification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='specification')
    certifications = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    material_family = models.CharField(max_length=100, blank=True, null=True)
    size_length = models.PositiveIntegerField(blank=True, null=True)
    size_width = models.PositiveIntegerField(blank=True, null=True)
    size_height = models.PositiveIntegerField(blank=True, null=True)
    warranty_duration = models.PositiveIntegerField(blank=True, null=True)
    warranty_type = models.CharField(max_length=100, blank=True, null=True)
    product_line = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} Specification"


class Pricing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='pricing')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sales_start_date = models.DateField()
    sales_end_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name} Pricing"
    
    def save(self, *args, **kwargs):
        if not self.sale_price:
            # Convert 0.05 to Decimal and calculate the sale price
            self.sale_price = self.base_price + (self.base_price * Decimal('0.05'))
        super().save(*args, **kwargs)

