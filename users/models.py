from django.db import models
import uuid, random
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'Admin')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser, PermissionsMixin):
    username = None
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    
    USER_TYPE_CHOICES = [
        ('Customer', 'Customer'),
        ('Vendor', 'Vendor')
    ]
    password = models.CharField(max_length=128)  # Increase length to accommodate hashed passwords
    retype_password = models.CharField(max_length=128, default="re_enter password")
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES, default='Customer')
    is_active = models.BooleanField(default=False)
    otp = models.CharField(max_length=4, blank=True, null=True)
    created_on = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS  = []
    def __str__(self):
        return self.email

    def generate_otp(self):
        import random
        otp = ''.join([str(random.randint(0,9)) for _ in range(4)])
        self.otp = otp
        self.save()
        return otp 

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256,blank=True, null=True)
    last_name = models.CharField(max_length=256,blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length = 10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Customer: {self.user.email}'
class Admin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=256,blank=True, null=True)
    last_name = models.CharField(max_length=256,blank=True, null=True)

    def __str__(self):
        return f'Admin: {self.user.email}'
class Vendor(models.Model):
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
class Newsletters(models.Model):
    id= models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #user=models.OneToOneField(User, on_delete=models.CASCADE)
    email=models.EmailField(unique=True)