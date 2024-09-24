from rest_framework import viewsets, status 
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import *
from .permissions import IsVendor
from rest_framework.decorators import action
from rest_framework.response import Response

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendor]


    @action(detail=False, methods=['post'], url_path='category', serializer_class = ProductCategorySerializer)
    def create_categories(self, request, *args, **kwargs):  
        serializer = ProductCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            "message": "Category Created Successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
        
        