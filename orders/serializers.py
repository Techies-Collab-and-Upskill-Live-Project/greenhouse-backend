from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'variation', 'quantity', 'subtotal']
        read_only_fields = ['subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'items', 'total_amount', 'created_at', 'updated_at']
        read_only_fields = ['customer', 'total_amount']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'created_at', 'status', 'total_amount', 'subtotal',
                  'vat_percentage', 'vat_amount', 'shipping_rate', 'shipping_address',
                  'payment_method', 'payment_status', 'shipping_method', 'items']
        read_only_fields = ['customer', 'total_amount', 'subtotal', 'vat_amount']

    def create(self, validated_data):
        # Calculate VAT amount
        subtotal = validated_data['subtotal']
        vat_percentage = validated_data['vat_percentage']
        vat_amount = subtotal * (vat_percentage / 100)
        
        # Calculate total amount
        shipping_rate = validated_data['shipping_rate']
        total_amount = subtotal + vat_amount + shipping_rate

        # Update the validated data
        validated_data['vat_amount'] = vat_amount
        validated_data['total_amount'] = total_amount

        return super().create(validated_data)