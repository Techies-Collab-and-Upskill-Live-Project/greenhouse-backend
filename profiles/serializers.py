from rest_framework import serializers
from .models import *


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorReg
        fields = ['account_type','shop_name','cac_Id','cac_certificate']

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerReg
        fields = ['first_name','last_name','street_address','city','postal_code']
