from rest_framework import serializers
from .models import *
from orders.models import *

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariation
        fields = ['id', 'seller_sku', 'barcode', 'quantity']
        read_only = ['seller_sku']

class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = [
            'id', 'certifications', 'model', 'material_family',
            'size_length', 'size_width', 'size_height',
            'warranty_duration', 'warranty_type', 'product_line', 'notes'
        ]

class PricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pricing
        fields = ['id', 'base_price', 'sale_price', 'sales_start_date', 'sales_end_date']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    variations = ProductVariationSerializer(many=True)
    specification = ProductSpecificationSerializer()
    pricing = PricingSerializer()
    category = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'sku', 'brand', 'status', 'color', 'description', 'weight', 'vendor',
            'images', 'variations', 'specification', 'pricing'
        ]
        read_only_fields = ['vendor']

    def create(self, validated_data):
        images_data = validated_data.pop('images')
        variations_data = validated_data.pop('variations')
        specification_data = validated_data.pop('specification')
        pricing_data = validated_data.pop('pricing')
        product = Product.objects.create(**validated_data)
        
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        
        for variation_data in variations_data:
            ProductVariation.objects.create(product=product, **variation_data)
        
        ProductSpecification.objects.create(product=product, **specification_data)
        Pricing.objects.create(product=product, **pricing_data)
        
        return product

#customer's actions
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
