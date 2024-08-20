# from django.db import models
# import uuid
# from django.db.models import Sum, F
# from products.models import Customer, Product

# class Order(models.Model):
#     DELIVERY_METHOD_CHOICES = [
#         ('Delivery', 'Delivery'),
#         ('Postal', 'Postal'),
#         ('Pickup', 'Pickup')
#     ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     delivery_method = models.CharField(max_length=50, choices=DELIVERY_METHOD_CHOICES, default='Delivery')
#     STATUS_CHOICES = [
#         ('Processing', 'Processing'),
#         ('Completed', 'Completed'),
#         ('Cancelled', 'Cancelled')
#     ]
#     status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Processing')
#     def __str__(self):
#         return f'Order {self.id} - {self.customer.user.username}'

#     @property
#     def total_price(self):
#         total = self.items.aggregate(
#             total_price=Sum(F('price') * F('quantity'))
#         )['total_price']
#         return total if total else 0

# class OrderItem(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f'OrderItem {self.id} - {self.menu.description}'
