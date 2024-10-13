
from rest_framework import serializers
from .models import *
from products.serializers import *

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variation = ProductVariationSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'variation', 'quantity', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'items', 'total_amount', 'created_at', 'updated_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variation = ProductVariationSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'variation', 'quantity', 'price', 'vendor']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'delivery_method', 'status', 'payment_status',
                 'payment_reference', 'total_amount', 'tracking_number', 'items',
                 'created_at', 'updated_at']
        
        
class AddItemSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    variation = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)

class UpdateItemQuantitySerializer(serializers.Serializer):
    item = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)

class RemoveItemSerializer(serializers.Serializer):
    item = serializers.UUIDField()