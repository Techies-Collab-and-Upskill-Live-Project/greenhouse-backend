from rest_framework import serializers
from .models import *

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()


# Serializer for setting the password
class SetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password1 = serializers.CharField(write_only=True)

# Serializer for completing the profile
class CompleteProfileSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20)

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


#Other actions
class ActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

class ResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self, email):
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("email not registered")
        return email

class ResetPasswordSerializer(serializers.Serializer):
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

    
    
# Vendor Registration Serializer
    
class VendorCountrySerializer(serializers.Serializer):
    country = serializers.CharField(max_length=100)

class VendorEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VendorRegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, default='Vendor')

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
class NewsletterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    class Meta:
        model = Newsletter
        fields = ['email']