from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User

class UserRegistrationTestCase(APITestCase):
    def test_registration(self):
        url = reverse('register')
        data = {
            'email': 'testuser@example.com',
            'password': 'strongpassword123',
            'usertype': 'Customer',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='testuser@example.com').exists())

    def test_registration_with_existing_email(self):
        User.objects.create_user(email='testuser@example.com', password='strongpassword123')
        url = reverse('user-register')
        data = {
            'email': 'testuser@example.com',
            'password': 'strongpassword123',
            'usertype': 'Customer',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



class UserActivationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='strongpassword123')
        self.user.activation_pin = '123456'
        self.user.save()

    def test_activation(self):
        url = reverse('user-activation')
        data = {
            'email': 'testuser@example.com',
            'activation_pin': '123456'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.activation_pin)

    def test_activation_with_invalid_pin(self):
        url = reverse('user-activation')
        data = {
            'email': 'testuser@example.com',
            'activation_pin': 'wrongpin'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
             
        
class UserLoginTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='strongpassword123')
        self.user.is_active = True
        self.user.save()

    def test_login(self):
        url = reverse('user-login')
        data = {
            'email': 'testuser@example.com',
            'password': 'strongpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_invalid_credentials(self):
        url = reverse('user-login')
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)