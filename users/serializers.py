from rest_framework import serializers
from .models import *

class  UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True)
    class Meta:
        model = User
        fields  = ['id', 'email', 'password', 'user_type']
        

class ActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    activation_pin = serializers.CharField(max_length=6)