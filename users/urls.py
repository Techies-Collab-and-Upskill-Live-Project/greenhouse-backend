from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
# router.register(r'profile', ProfileViewSet, basename='user_profile')
router.register(r'vendor', VendorViewSet, basename='vendor')

urlpatterns = [
    path('', include(router.urls)),
]


