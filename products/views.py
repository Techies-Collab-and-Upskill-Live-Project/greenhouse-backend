from rest_framework import viewsets, status 
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product
from .serializers import *
from .permissions import *
from rest_framework.decorators import action
from rest_framework.response import Response
import csv
from django.http import HttpResponse
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.template.loader import get_template
from xhtml2pdf import pisa

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
        
    permission_classes = [IsAuthenticated, IsVendor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['category', 'brand', 'color', 'vendor', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_on', 'price']

    def perform_create(self, serializer):
        vendor = Vendor.objects.get(user=self.request.user)
        serializer.save(vendor=vendor)
        
        
    @action(detail=False, methods=['get'], url_path='listing', permission_classes=[AllowAny])
    def product_listing(self, request):
        queryset = self.filter_queryset(self.get_queryset())  # Use the filtering, search, and ordering
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)



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
            category = product.category if product.category else 'No Category'

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
        Get the authenticated vendor
        vendor = Vendor.objects.get(user=request.user)

        Get all products created by this vendor
       products = Product.objects.filter(vendor=vendor)

        Define the template to render
        template = get_template('products/pdf_template.html')

        Prepare the data context for the template
        context = {
           'products': products
       }

        Render the HTML content
        html = template.render(context)

        Create a response object to hold the PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="vendor_products_export.pdf"'

        Convert HTML content to PDF
        pisa_status = pisa.CreatePDF(html, dest=response)

        If there's an error during PDF creation
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
