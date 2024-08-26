from rest_framework import serializers
from .models import *


#def password_validator(self, password):
 #   if len(password) <8:
  #      raise serializer.ValidationError("Password too short")
   # return password


class  UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True)
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

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
    email = serializers.EmailField()
    def save(self, **kwargs):
        email= self.validated_data['email']
        new_password = self.validated_data['new_password']
        user = User.objects.get(email = email)
        user.set_password(new_password)
        user.otp = None
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
class VendorCountrySerializer(serializers.Serializer):
    country = serializers.CharField(max_length=100)
    
class VendorEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    

class VendorRegistrationSerializer(serializers.ModelSerializer):
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, default='Vendor',)

    class Meta:
        model = User
        fields = ('phone_number', 'password', 'user_type',)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Email and country are added here from the session
        validated_data['email'] = self.context['request'].session['email_verified']
        validated_data['country'] = self.context['request'].session['country']
        user = User.objects.create_user(**validated_data)
        return user
    
    def __init__(self, *args, **kwargs):
        super(VendorRegistrationSerializer, self).__init__(*args, **kwargs)
        self.fields['user_type'].initial = 'Vendor'
        
        
class FlexibleVendorShopSerializer(serializers.ModelSerializer):
    account_type = serializers.ChoiceField(choices=Vendor.ACCOUNT_TYPE_CHOICES)
    cac_id = serializers.CharField(required=False)
    cac_certificate = serializers.FileField(required=False)
    

    class Meta:
        model = Vendor
        fields = ['account_type', 'shop_name', 'where_you_hear', 'policy_agreement', 'shipping_zone', 
                  'cac_id', 'cac_certificate', 'updated_at']

    def validate(self, data):
        account_type = data.get('account_type')
        
        if account_type == 'Business':
            if not data.get('cac_id'):
                raise serializers.ValidationError({"cac_id": "CAC ID is required for Business accounts."})
            if not data.get('cac_certificate'):
                raise serializers.ValidationError({"cac_certificate": "CAC Certificate is required for Business accounts."})
        elif account_type == 'Individual':
            # Remove business-specific fields if they're provided
            data.pop('cac_id', None)
            data.pop('cac_certificate', None)
        
        return data
