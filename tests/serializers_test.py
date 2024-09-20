import pytest
from users.serializers import *
from rest_framework.exceptions import ValidationError
from users.models import *

@pytest.mark.django_db
def test_non_matching():
    data = {'email': "email@example.com", 'phone_number': "1234567890", 'password':'password', 'retype_password': 'repassword', 'country': 'Nigeria', 'user_type' : 'Customer'}
    serializer = UserSerializer(data=data)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert 'Passwords do not match' in str(exc_info.value)


@pytest.mark.django_db
def test_matching_mail():
    data = {'email': "email@example.com", 'phone_number': "1234567890", 'password':'password', 'retype_password': 'password', 'country': 'Nigeria', 'user_type' : 'Customer'}
    serializer = UserSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    assert serializer.is_valid()
    validated_data=serializer.validated_data
    assert validated_data['password']=="password"

@pytest.mark.django_db
def test_wrong_email():
    data= {'email':"wrongmail@example.com"}
#    user=User.objects.get(data=data)
    serializer=ResetrequestSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    assert serializer.is_valid()
    validated_data=serializer.validated_data
    assert validated_data['email'] == 'wrongmail@example.com'

@pytest.mark.django_db
def test_unregistered_email():
    data= {'email':"email@example.com"}
    serializer=ResetrequestSerializer(data=data)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert 'email not registered' in str(exc_info.value)
