from rest_framework import serializers
from .models import User

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

class ActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    activation_pin = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    
# class VendorEmailRegistration(serializers.Serializer):
#     email = serializers.EmailField()
    
