from rest_framework import viewsets, status 
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product
from .serializers import *
from .permissions import IsVendor
from rest_framework.decorators import action
from rest_framework.response import Response
import csv
from django.http import HttpResponse
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.template.loader import get_template
from xhtml2pdf import pisa
from rest_framework.exceptions import ValidationError
# from rest_framework.generics import ListAPIView, 
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin




class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
#    permission_classes = [IsAuthenticated, IsVendor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['category', 'brand', 'color', 'vendor', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_on', 'price']

    def get_queryset(self):
        try:
            vendor = Vendor.objects.get(user=self.request.user)
            return Product.objects.filter(vendor=vendor)
        except Vendor.DoesNotExist:
            return Product.objects.none()

    def perform_create(self, serializer):
        try:
            # Get the vendor for the authenticated user
           # vendor = Vendor.objects.get(user=self.request.user)
            
            # Save the product with vendor
            product = serializer.save()#vendor=vendor)
            
            # Handle multiple image uploads
            images_data = self.request.FILES.getlist('images', [])
            image_instances = []
            
            for image_data in images_data:
                # Validate image size and format if needed
                if self._validate_image(image_data):
                    image_instance = ProductImage.objects.create(
                        product=product,
                        image=image_data
                    )
                    image_instances.append(image_instance)
            
            # Prepare response data
            response_data = serializer.data
            response_data['images'] = ProductImageSerializer(image_instances, many=True).data
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Vendor.DoesNotExist:
            raise ValidationError({"error": "Vendor profile not found for this user"})
        except Exception as e:
            # Delete the product if image handling fails
            if 'product' in locals():
                product.delete()
            raise ValidationError({"error": f"Error creating product: {str(e)}"})

    def _validate_image(self, image):
        """
        Validate image file size and format
        Returns True if valid, False otherwise
        """
        # Maximum file size (5MB)
        MAX_SIZE = 5 * 1024 * 1024
        
        # Allowed file types
        ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
        
        # Check file size
        if image.size > MAX_SIZE:
            raise ValidationError({
                "error": f"Image size should not exceed {MAX_SIZE/1024/1024}MB"
            })
            
        # Check file type
        if hasattr(image, 'content_type') and image.content_type not in ALLOWED_TYPES:
            raise ValidationError({
                "error": f"Invalid image format. Allowed formats: {', '.join(ALLOWED_TYPES)}"
            })
            
        return True

    def perform_update(self, serializer):
        """
        Override perform_update to handle image updates
        """
        try:
            instance = serializer.save()
            
            # Handle image updates if new images are provided
            images_data = self.request.FILES.getlist('images', [])
            if images_data:
                # Optionally clear existing images if needed
                # instance.images.all().delete()
                
                image_instances = []
                for image_data in images_data:
                    if self._validate_image(image_data):
                        image_instance = ProductImage.objects.create(
                            product=instance,
                            image=image_data
                        )
                        image_instances.append(image_instance)
                
                # Update response data with new images
                response_data = serializer.data
                response_data['images'] = ProductImageSerializer(
                    instance.images.all(),
                    many=True
                ).data
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            raise ValidationError({"error": f"Error updating product: {str(e)}"})

    
    

    # Export action
    @action(detail=False, methods=['get'], url_path='export/csv', permission_classes=[IsAuthenticated, IsVendor])
    def export_products(self, request):
        # Get the authenticated vendor
        vendor = Vendor.objects.get(user=request.user)

        # Get all products created by this vendor
        products = Product.objects.filter(vendor=vendor)

        # Create the HTTP response with CSV headers
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="vendor_products_export.csv"'

        # Create the CSV writer
        writer = csv.writer(response)
        
        # Write the header row
        writer.writerow(['Name', 'SKU', 'Price', 'Category', 'Quantity', 'Status'])

        # Write data rows for each product
        for product in products:
            # Fetch related pricing and variations
            price = product.pricing.sale_price if product.pricing and product.pricing.sale_price else product.pricing.base_price if product.pricing else 'No Price'
            quantity = product.variations.first().quantity if product.variations.exists() else 'No Quantity'
            category = product.category.name if product.category else 'No Category'

            writer.writerow([
                product.name,  # Product name
                product.sku,  # SKU
                price,  # Price from Pricing model
                category,  # Category from Product model
                quantity,  # Quantity from ProductVariation model
                product.status  # Status (active/inactive)
            ])

        return response
    
    @action(detail=False, methods=['get'], url_path='export/pdf', permission_classes=[IsAuthenticated, IsVendor])
    def export_products_pdf(self, request):
        # Get the authenticated vendor
        vendor = Vendor.objects.get(user=request.user)

        # Get all products created by this vendor
        products = Product.objects.filter(vendor=vendor)

        # Define the template to render
        template = get_template('products/pdf_template.html')

        # Prepare the data context for the template
        context = {
            'products': products
        }

        # Render the HTML content
        html = template.render(context)

        # Create a response object to hold the PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="vendor_products_export.pdf"'

        # Convert HTML content to PDF
        pisa_status = pisa.CreatePDF(html, dest=response)

        # If there's an error during PDF creation
        if pisa_status.err:
            return HttpResponse('We had some errors generating the PDF', status=500)
        
        return response



    @action(detail=False, methods=['post'], url_path='category', serializer_class = ProductCategorySerializer)
    def create_categories(self, request, *args, **kwargs):  
        serializer = ProductCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Category Created Successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
        
        
        #  Action to get all categories
    @action(detail=False, methods=['get'], url_path='categories-list', serializer_class=ProductCategorySerializer)
    def list_categories(self, request, *args, **kwargs):
        # Query all categories
        categories = Category.objects.all()

        # Serialize the categories
        serializer = ProductCategorySerializer(categories, many=True)

        # Return serialized data
        return Response({
            "message": "Categories retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
        
        
class ProductListViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    # Adding filtering backends for the list view
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'color', 'vendor', 'status']  # example fields for filtering
    search_fields = ['name', 'description']   # fields for search
    ordering_fields = ['price', 'created_at'] # fields for ordering
    
    def list(self, request, *args, **kwargs):
        # Customize the listing response with additional URLs for each product
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        
        # Add additional URLs to each product in the listing
        product_data_list = serializer.data
        
        return Response(product_data_list)
    
    def retrieve(self, request, *args, **kwargs):
        # Retrieve a single product with additional URLs in the response
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        
        product_data = serializer.data
        
        return Response(product_data)
