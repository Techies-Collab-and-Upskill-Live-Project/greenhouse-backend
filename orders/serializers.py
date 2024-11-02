from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only = True,)
    product_id = serializers.UUIDField(required=True)
    variation_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'variation_id', 'quantity', 'subtotal']
        read_only_fields = ['subtotal']
        
        
        def validate(self, data):
        # Add any additional validation logic here
            if data.get('quantity', 1) < 1:
                raise serializers.ValidationError("Quantity must be at least 1")
            return data

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'items', 'total_amount', 'created_at', 'updated_at']
        read_only_fields = ['customer', 'total_amount']
        
        
class RemoveCartItemSerializer(serializers.Serializer):
    cart_item_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(required=False, min_value=1)

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