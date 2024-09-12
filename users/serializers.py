from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    retype_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id','email', 'phone_number', 'password', 'retype_password', 'country', 'user_type')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def validate(self, data):
        if data['password'] != data['retype_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

#Registrations based on user_type

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['account_type','shop_name','cac_id','cac_certificate']

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['first_name','last_name','street_address','city','postal_code']

#additional registration details based on user_type
#class ExtendRegSerializer(serializers.Serializer):
   # def get_serializer_class(self, user_type):
    #    if user_type == 'Customer':
     #       return CustomerRegistrationSerializer
      #  if user_type == 'Admin':
       #     return AdminRegistrationSerializer
        #else:
         #   return VendorRegistrationSerializer
    #def create ()
     #   class meta:
      #  model = User
        #fields = []

#Other actions
class ActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    activation_pin = serializers.CharField(max_length=6)

class ResetrequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validator(self, email):
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("email not registered")
        return email

class ResetpasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length = 6)
    new_password = serializers.CharField(max_length = 255, write_only = True)
    password_again = serializers.CharField(max_length = 255, write_only = True)
    email = serializers.EmailField()
    
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=10, required=True, write_only=True)
    new_password = serializers.CharField(max_length=10, required=True, write_only=True)
    confirm_new_password = serializers.CharField(max_length=10, required=True, write_only=True)

    def validate(self, data):
        if data.get('new_password') != data.get('confirm_new_password'):
            raise serializers.ValidationError('New Password do not match')
        user = self.context['request'].user
        if not user.check_password(data.get('current_password')):
            raise serializers.ValidationError('Incorrect current password')
        return data

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
class VendorCountrySerializer(serializers.Serializer):
    country = serializers.CharField(max_length=100)
    
class VendorEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
class FlexibleVendorShopSerializer(serializers.ModelSerializer):
    account_type = serializers.ChoiceField(choices=Vendor.ACCOUNT_TYPE_CHOICES)
    cac_id = serializers.CharField(required=False)
    cac_certificate = serializers.FileField(required=False)
    email = serializers.EmailField(read_only=True)
    country = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = Vendor
        fields = ['account_type', 'shop_name', 'where_you_hear', 'policy_agreement', 'shipping_zone', 
                  'cac_id', 'cac_certificate', 'email', 'country', 'phone_number']

    def validate(self, data):
        account_type = data.get('account_type')
        
        if account_type == 'Business':
            if not data.get('cac_id'):
                raise serializers.ValidationError({"cac_id": "CAC ID is required for Business accounts."})
            if not data.get('cac_certificate'):
                raise serializers.ValidationError({"cac_certificate": "CAC Certificate is required for Business accounts."})
        elif account_type == 'Individual':
            data.pop('cac_id', None)
            data.pop('cac_certificate', None)
        
        return data
