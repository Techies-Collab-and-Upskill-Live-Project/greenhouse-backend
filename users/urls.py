from django.urls import path
from .views import *

urlpatterns = [
    path('register', UserRegistrationView.as_view(), name='register'),
    path('activate', ActivationView.as_view(), name='activate_user'),
    path('resetrequest', ResetrequestView.as_view(), name='resetrequest'),
    path('resetpassword', ResetpasswordView.as_view(), name='resetpassword'),
    
]

