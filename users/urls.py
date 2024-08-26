from django.urls import path
from .views import *

urlpatterns = [
    path('register', UserRegistrationView.as_view(), name='register'),
    path('activate', ActivationView.as_view(), name='activate_user'),
    path('login', LoginView.as_view(), name='token_generation'),
    path('change-password', ChangePasswordView.as_view(), name='change_passsword')
    
]

