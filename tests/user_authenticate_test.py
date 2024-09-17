import pytest
from django.urls import reverse
from rest_framework.test import APIClient
#from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model


User=get_user_model()

@pytest.mark.django_db
def test_authenticated():
# This is to check if the user is authenticated
# Create a dummy user
    user = User.objects.create_user(email='testuser@example.com', password='testpass')
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    url = reverse('user-detail', kwargs={'pk': user.pk})
    response = client.get(url)
    assert response.status_code == 200
#    assert response.data == {"message": "Authenticated!"}

