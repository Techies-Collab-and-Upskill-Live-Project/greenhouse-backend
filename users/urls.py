from django.urls import path
from .views import *

urlpatterns = [
    path('register', UserRegistrationView.as_view(), name='register'),
    path('activate', ActivationView.as_view(), name='activate_user'),
    
]

