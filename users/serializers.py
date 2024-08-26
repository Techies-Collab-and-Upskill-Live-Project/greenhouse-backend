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
    
class ChangePasswodSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=10, required=True, write_only=True)
    new_password = serializers.CharField(max_length=10, required=True, write_only=True)
    confirm_new_pasword = serializers.CharField(max_length=10, required=True, write_only=True)

    def validate(self, data):
        if data.get('new_password') != data.get('confirm_new_password'):
            raise serializers.ValidationError('New Password do not match')
        user = self.context['request'].user
        if not user.check_password(data.get('current_password')):
            raise serializers.ValidationError('Incorrect current password')
        return data