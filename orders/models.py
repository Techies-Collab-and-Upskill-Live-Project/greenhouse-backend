from django.db import models
import uuid
from django.db.models import Sum, F
from products.models import Product
from users.models import User

class Order(models.Model):
    DELIVERY_METHOD_CHOICES = [
            ('Delivery', 'Delivery'),
            ('Postal', 'Postal'),
            ('Pickup', 'Pickup')
            ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.OneToOneField('Cart', on_delete=models.CASCADE, null = True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_method = models.CharField(max_length=50, choices=DELIVERY_METHOD_CHOICES, default='Delivery')
    STATUS_CHOICES = [
            ('Processing', 'Processing'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled')
            ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Processing')
    def __str__(self):
        return f'Order {self.id} - {self.customer.user.username}'
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null = True)
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, null = True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'OrderItem {self.id} - {self.menu.description}'
