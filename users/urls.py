from django.urls import path
from .views import *

urlpatterns = [
    path('register', UserRegistrationView.as_view(), name='register'),
    path('activate', ActivationView.as_view(), name='activate_user'),
    path('login', LoginView.as_view(), name='token_generation'),
    path('vendor/country', VendorCountryView.as_view(), name='select-country'),
    path('vendor/email', VendorEmailSubmissionView.as_view(), name='submit-email'),
    path('vendor/activate', VendorOTPVerificationView.as_view(), name='activate-vendor'),
    path('vendor/register', VendorRegistrationView.as_view(), name='register-vendor'),
    path('vendor/update', VendorShopUpdateView.as_view(), name='individual-vendor'),

]

