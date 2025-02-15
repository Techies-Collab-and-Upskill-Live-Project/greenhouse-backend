from rest_framework import serializers
from .models import *

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url']

    def get_image_url(self, product_image):
        # Check if product_image.image exists before accessing url
        return product_image.image.url if product_image.image else None

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
        read_only_fields = ['sale_price']
        

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)  # Only read image URLs
    variations = ProductVariationSerializer(many=True)
    specification = ProductSpecificationSerializer()
    pricing = PricingSerializer()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'sku', 'brand', 'status', 'color', 'description', 'weight', 'vendor',
            'images', 'variations', 'specification', 'pricing'
        ]
        read_only_fields = ['vendor']

    def create(self, validated_data):
        # Handle non-image nested data
        variations_data = validated_data.pop('variations', [])
        specification_data = validated_data.pop('specification', None)
        pricing_data = validated_data.pop('pricing', None)
        
        # Create the product
        product = Product.objects.create(**validated_data)
        
        # Create related objects
        for variation_data in variations_data:
            ProductVariation.objects.create(product=product, **variation_data)
        
        ProductSpecification.objects.create(product=product, **specification_data)
        Pricing.objects.create(product=product, **pricing_data)
        
        return product
