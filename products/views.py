from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import ProductSerializer
from .permissions import IsVendor
from rest_framework.decorators import action
from rest_framework.decorators import action

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    @action(detail = False, methods =['post'], url_path = 'upload')
    

    def upload(self, request):
        serializer.save(vendor=self.request.user.vendor)
