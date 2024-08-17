from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    USER_TYPE_CHOICES = [
        ('Customer', 'Customer'),
        ('Admin', 'Admin'),
        ('Vendor', 'Vendor')
    ]
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES, default='Customer')
    is_active = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Customer: {self.user.username}'

class Admin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Admin: {self.user.username}'


class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Vendor: {self.user.username}'

#create and save user profile signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'Customer':
        Customer.objects.create(user=instance)
    elif created and instance.user_type == 'Admin':
        Admin.objects.create(user=instance)
    elif created and instance.user_type == 'Vendor':
        Vendor.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 'Customer' and hasattr(instance, 'customer'):
        instance.customer.save()
    elif instance.user_type == 'Admin' and hasattr(instance, 'admin'):
        instance.admin.save()
    elif instance.user_type == 'Vendor' and hasattr(instance, 'vendor'):
        instance.vendor.save()
