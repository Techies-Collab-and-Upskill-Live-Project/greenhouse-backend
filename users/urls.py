from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
#router.register(r'login', LoginViewSet, basename='login')
#router.register(r'change-password', ChangePasswordViewSet, basename='change-password')
#router.register(r'vendor/country', VendorCountryViewSet, basename='vendor-country')
#router.register(r'vendor/shop', FlexibleVendorShopViewSet, basename='FlexibleVendor')
#router.register(r'extendreg', ExtendRegViewSet, basename='extend-reg')
urlpatterns = [
    path('', include(router.urls)),
]

