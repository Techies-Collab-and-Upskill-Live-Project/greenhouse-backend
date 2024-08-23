from rest_framework import serializers
from .models import *

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

class ResetpasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length = 6)
    new_password = serializers.CharField(max_length = 255, write_only = True)
    email = serializers.EmailField()
    #class Meta: 
      #  model = User
       # fields = ['email', 'otp', 'new_password']

    def validator(self, data):
        email = data.get(email)
        otp = data.get(otp)
        #validate if email exist
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializer.ValidationError("invalid email")
        if user.otp != otp:
            raise serializer.ValidationError("invalid OTP")
        return data
    def safe(self):
        email = self.Validated_data['email']
        new_password = self.Validated_data['new_password']
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.otp = None
        user.save()
        return user

