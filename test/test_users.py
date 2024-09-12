from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from unittest.mock import patch

class UserRegistrationViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')

    def test_user_registration_success(self):
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        with patch('django.core.mail.send_mail') as mock_send_mail:
            response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "User registered successfully. OTP sent to your email")
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        mock_send_mail.assert_called_once()

    def test_user_registration_existing_email(self):
        User.objects.create_user(email='existing@example.com', password='existingpassword123')
        data = {
            'email': 'existing@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error'], "User with this email already exists")

class ActivationViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.activate_url = reverse('activate_user')
        self.user = User.objects.create_user(email='test@example.com', password='testpassword123')
        self.user.is_active = False
        self.user.activation_pin = '123456'
        self.user.save()

    def test_activation_success(self):
        data = {
            'email': 'test@example.com',
            'activation_pin': '123456'
        }
        response = self.client.post(self.activate_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Account activated successfully!")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.activation_pin)

    def test_activation_invalid_pin(self):
        data = {
            'email': 'test@example.com',
            'activation_pin': '654321'
        }
        response = self.client.post(self.activate_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Invalid activation PIN.")

    def test_activation_user_not_found(self):
        data = {
            'email': 'nonexistent@example.com',
            'activation_pin': '123456'
        }
        response = self.client.post(self.activate_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "User not found.")

class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('token_generation')
        self.user = User.objects.create_user(email='test@example.com', password='testpassword123')
        self.user.is_active = True
        self.user.save()

    def test_login_success(self):
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

    def test_login_invalid_credentials(self):
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)