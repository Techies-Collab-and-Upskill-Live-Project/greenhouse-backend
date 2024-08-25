from django.db import models
<<<<<<< HEAD
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid, random
=======
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
import uuid
>>>>>>> a0b1ecb65b234072b194dae4fc7e20fe438c63ae
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
        ('Admin', 'Admin'),
        ('Vendor', 'Vendor')
    ]
    #password = models.CharField(max_length = 8, write_only = True)
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES, default='Customer')
    is_active = models.BooleanField(default=False)
    activation_pin = models.CharField(max_length = 6, blank=True, null=True)
    otp = models.CharField(max_length = 6, blank=True, null=True)
    created_on = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS  = []
    
    def __str__(self):
        return self.email
    
    def generate_activation_pin(self):
#        import random
        pin = ''.join([str(random.randint(0,9)) for _ in range(6)])
        self.activation_pin = pin
        self.save()
        
    def generate_otp(self):
        import random
        pin = ''.join([str(random.randint(0,9)) for _ in range(6)])
        self.otp = pin
        self.save()
        return pin

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256,blank=True, null=True)
    last_name = models.CharField(max_length=256,blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length = 10, blank=True, null=True)
    account_number = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Customer: {self.user.email}'

class Admin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

#create and save user profile signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'Customer':
        Customer.objects.create(user=instance)
    elif created and instance.user_type == 'Admin':
        instance.is_staff = True
        instance.is_superuser = True
        instance.save()
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
