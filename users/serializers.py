from rest_framework import serializers
from .models import *


def password_validator(self, password):
    if len(password) <8:
        raise serializer.ValidationError("Password too short")
    return password


class  UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True)
    class Meta:
        model = User
        fields  = ['id', 'email', 'password', 'user_type']
        

class ActivationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    activation_pin = serializers.CharField(max_length=6)
    class Meta:
        model = User
        fields = ['email', 'activation_pin']


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
