from rest_framework import viewsets, status
from .serializers import *
from .models import *
from products.models import *
from products.serializers import *
from django.http import HttpResponse
from rest_framework.decorators import action
from products.permissions import *

class CartViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=Product.objects.all()
    serializer_class=CartSerializer
    permission_classes = [IsCustomer]
    def get_serializer_class(self):
        if self.action == "add_to_cart":
            return CartSerializer
        elif self.action == "order":
            return OrderSerializer
        return CartSerializer

    #place orders
    @action(detail=True, methods=['post'], url_path='add_to_cart', permission_classes=[IsCustomer])
    def add_to_cart(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        cart = request.data.get('cart')
        quantity = request.data.get('product', 0)
        order, created=Order.objects.get_or_create(customer=request.user)
        cart, cart_create = CartItem.objects.get_or_create(cart=cart, product=cart_item)
        if not item_create:
            cart_item +=int(quantity)
            cart_item.save()
        else:
            cart_item.quantity = quantity
            cart_item.price = product.price
            cart_item.save()
        serializer = CartSerializer(cart)
        return Response({"success":True,
            "message": f"{product.name} added to cart",
            "data": serializer.data
            },
            status_code = status.HTTP_201_CREATED)

#ZZclass OrderViewSet(viewsets.ModelViewSet):
   # queryset=Product.objects.all()
    #serializer_class=OrderSerializer
    @action(detail=True, methods=['post'], url_path='order', permission_classes=[IsCustomer])
    def order(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart =Cart.objects.get(customer=request.user)
        if not cart:
            return Response({"success":False, "message":"Cart is currently empty"}, status=status.HTTP_400_BAD_REQUEST)
        total_cost = sum(cart_item.product.price * cart_item.quantity for cart_item in cart)
        order = Order.objects.create(user=user, total_price=total_cost, status="pending")
        for cart_item in carts.items.all():
            cart_item.order = order
            cart_item.save()
            cart.delete()
        serializer = OrderSerializer(order)
        return Response({
            "success": True,
            "message": "Order has been created successfully",
            "data": serializer.data
            },
            status=status.HTTP_201_CREATED)
