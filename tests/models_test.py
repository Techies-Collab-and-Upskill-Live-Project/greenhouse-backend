import pytest
from users.models import *
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

manager=CustomUserManager()
@pytest.mark.django_db
def test_blank_email():
    manager=CustomUserManager()
    with pytest.raises(ValueError) as exc_info:
         manager.create_user(email='', password = 'password')
    assert 'The Email field must be set' in str(exc_info.value)

@pytest.mark.django_db
def test_extra_fields():
    user=User.objects.create_superuser(email='example@email.com', password='password')
    assert user.is_superuser
    assert user.is_active
    assert user.is_staff
    assert user.user_type == "Admin"

@pytest.mark.django_db
def test_User():
    user=User.objects.create(email="example@email.com", phone_number='1234567890', country='Nigeria', password='password', retype_password='password', user_type= 'Customer',otp = '123456')

    assert user.email == "example@email.com"
    assert user.phone_number == "1234567890"
    assert user.country == "Nigeria"
    assert user.password == "password"
    assert user.retype_password == "password"
    assert user.user_type == "Customer"
    assert user.otp == "123456"

@pytest.mark.django_db
def test_user_string():
    user=User.objects.create(email="example@email.com", password='password', retype_password='password')
    assert str(user)== "example@email.com"

@pytest.mark.django_db
def test_otp_gen():
     user=User.objects.create(email="example@email.com", password='password', retype_password='password')
     otp=user.generate_otp()
     assert len(otp) == 6
     assert otp.isdigit()
     user.refresh_from_db()
     assert user.otp == otp

@pytest.mark.django_db
def test_customer_string():
    user=User.objects.create(email="example@email.com", password='password')
    customer = Customer.objects.create(user=user)
    assert str(customer)== f"Customer: {user.email}"


@pytest.mark.django_db
def test_admin_string():
    user=User.objects.create(email="example@email.com", password='password')
    admin = Admin.objects.create(user=user)
    assert str(admin)== f"Admin: {user.email}"

@pytest.mark.django_db
def test_vendor_string():
    user=User.objects.create(email="example@email.com", password='password')
    vendor = Vendor.objects.create(user=user)
    assert str(vendor)== f"Vendor: {user.email}"
