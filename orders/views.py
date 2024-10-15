from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, AddItemSerializer, RemoveItemSerializer, UpdateItemQuantitySerializer, OrderSerializer
from products.permissions import IsCustomer
from products.models import Product, ProductVariation
from .utils import create_paystack_payment_link  
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

from rest_framework.exceptions import NotFound

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [AllowAny,]

    def get_queryset(self):
        return Cart.objects.filter(customer=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.first()
        if not obj:
            raise NotFound("No cart found for this customer.")
        return obj

    def create(self, request):
        # This method is now essentially a "get or create"
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product': openapi.Schema(type=openapi.TYPE_INTEGER),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                'variation': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['product', 'quantity']
        )
    )
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_object()
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        
        product = get_object_or_404(Product, id=product_id)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, 
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        cart_serializer = self.get_serializer(cart)
        return Response(cart_serializer.data)
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'item': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        serializer = RemoveItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item_id = serializer.validated_data['item']
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        cart_serializer = self.get_serializer(cart)
        return Response(cart_serializer.data)
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'item': openapi.Schema(type=openapi.TYPE_INTEGER),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )

    @action(detail=True, methods=['post'])
    def update_item_quantity(self, request, pk=None):
        cart = self.get_object()
        serializer = UpdateItemQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item_id = serializer.validated_data['item']
        new_quantity = serializer.validated_data['quantity']

        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.quantity = new_quantity
        cart_item.save()

        cart_serializer = self.get_serializer(cart)
        return Response(cart_serializer.data)

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        cart = self.get_object()
        cart.items.all().delete()
        cart_serializer = self.get_serializer(cart)
        return Response(cart_serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsCustomer]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'delivery_method': openapi.Schema(type=openapi.TYPE_STRING, default='Delivery'),
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Order created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'order': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'payment_link': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            status.HTTP_400_BAD_REQUEST: "Cart is empty",
        }
    )

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_from_cart(self, request):
        cart = get_object_or_404(Cart, customer=request.user)
        if not cart.items.exists():
            raise ValidationError('Cart is empty')

        order_data = {
            'customer': request.user.id,
            'delivery_method': request.data.get('delivery_method', 'Delivery'),
            'total_amount': cart.total_amount
        }
        
        # Validate and create the order
        order_serializer = OrderSerializer(data=order_data)
        order_serializer.is_valid(raise_exception=True)
        order = order_serializer.save()

        # Create OrderItems from CartItems
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variation=cart_item.variation,
                quantity=cart_item.quantity,
                price=cart_item.product.pricing.sale_price or cart_item.product.pricing.base_price,
                vendor=cart_item.product.vendor
            )

        # Clear the cart after order creation
        cart.items.all().delete()

        # Paystack payment integration
        payment_link = create_paystack_payment_link(order)  
        order.payment_reference = payment_link['reference']
        order.save()

        return Response({
            'order': order_serializer.data,
            'payment_link': payment_link['authorization_url']
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        raise ValidationError('Invalid status')

    @action(detail=True, methods=['get'])
    def get_order_details(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def get_user_orders(self, request):
        orders = self.get_queryset().order_by('-created_at')
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        if order.status == 'Pending':
            order.status = 'Cancelled'
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        raise ValidationError('Order cannot be cancelled')

    



@csrf_exempt
def paystack_webhook(request):
    # Only allow POST requests
    if request.method == 'POST':
        # Retrieve the event payload
        payload = json.loads(request.body)
        event = payload.get('event')
        data = payload.get('data', {})
        
        # Get the reference and order
        reference = data.get('reference')
        try:
            order = Order.objects.get(payment_reference=reference)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=400)

        # Handle different Paystack events
        if event == 'charge.success':
            # Verify the payment status
            if data.get('status') == 'success':
                # Mark order as paid
                order.payment_status = 'Paid'
                order.status = 'Processing'
                order.save()
                return JsonResponse({'status': 'success', 'message': 'Payment successful'}, status=200)
        
        elif event == 'charge.failed':
            # Mark order as failed
            order.payment_status = 'Failed'
            order.status = 'Cancelled'
            order.save()
            return JsonResponse({'status': 'error', 'message': 'Payment failed'}, status=200)
        
        # Handle other events if needed (e.g., 'charge.dispute', etc.)

        return JsonResponse({'status': 'success', 'message': 'Event processed'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
