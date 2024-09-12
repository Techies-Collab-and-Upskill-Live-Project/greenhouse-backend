from django.db import models
from users.models import User
import uuid, random

class AdminReg(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=256,blank=True, null=True)
    last_name = models.CharField(max_length=256,blank=True, null=True)

    def __str__(self):
        return f'Admin: {self.user.email}'

class CustomerReg(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256,blank=True, null=True)
    last_name = models.CharField(max_length=256,blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length = 10, blank=True, null=True)
#    account_number = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Customer: {self.user.email}'

class VendorReg(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ACCOUNT_TYPE_CHOICES = [
        ('Business', 'Business'),
        ('Individual', 'Individual')
    ]
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES, default='Individual', blank=True, null=True)
    shop_name = models.CharField(max_length = 255, blank=True, null=True)
    shipping_zone = models.CharField(max_length = 255, blank=True, null=True)
    where_you_hear = models.CharField(max_length=256,blank=True, null=True)
    policy_agreement  = models.BooleanField(default=False)
    cac_id = models.CharField(max_length=10,blank=True, null=True)
    cac_certificate = models.FileField(upload_to='cac_certificates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Vendor: {self.user.email}'


# Create your models here.
