from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'vendor', VendorViewSet, basename='vendor')
router.register(r'newsletter', NewsletterViewSet, basename='newsletter')
urlpatterns = [
    path('', include(router.urls)),
]

            

