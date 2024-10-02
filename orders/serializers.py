from rest_framework import serializers
from .models import *

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id','product', 'quantity']
class CartSerializer(serializers.ModelSerializer):
    cart_item=CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ['id','customer', 'cart_item']

class OrderSerializer(serializers.ModelSerializer):
    cart=CartSerializer(read_only=True)
    class Meta:
        model= Order
        fields = ['id', 'status', 'cart','created_at', 'updated_at']
