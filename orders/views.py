from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .serializers import *
from products.permissions import *
from .models import Cart, CartItem, Order, OrderItem
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist



class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return Cart.objects.filter(customer=self.request.user)

    def create(self, request):
        cart, created = Cart.objects.get_or_create(customer=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product']
        variation_id = serializer.validated_data.get('variation')
        quantity = serializer.validated_data['quantity']
        
        try:
            product = Product.objects.get(id=product_id)
            variation = ProductVariation.objects.get(id=variation_id) if variation_id else None
        except ObjectDoesNotExist:
            raise ValidationError('Invalid product or variation')
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variation=variation,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        cart_serializer = self.get_serializer(cart)
        return Response(cart_serializer.data)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        serializer = RemoveItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item_id = serializer.validated_data['item']
        
        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()
            cart_serializer = self.get_serializer(cart)
            return Response(cart_serializer.data)
        except CartItem.DoesNotExist:
            raise ValidationError('Item not found in cart')

    @action(detail=True, methods=['post'])
    def update_item_quantity(self, request, pk=None):
        cart = self.get_object()
        serializer = UpdateItemQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item_id = serializer.validated_data['item']
        new_quantity = serializer.validated_data['quantity']

        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.quantity = new_quantity
            cart_item.save()
            cart_serializer = self.get_serializer(cart)
            return Response(cart_serializer.data)
        except CartItem.DoesNotExist:
            raise ValidationError('Item not found in cart')

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        cart = self.get_object()
        cart.items.all().delete()
        cart_serializer = self.get_serializer(cart)
        return Response(cart_serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsCustomer]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_from_cart(self, request):
        try:
            cart = Cart.objects.get(customer=request.user)
            if not cart.items.exists():
                raise ValidationError('Cart is empty')

            order_data = {
                'customer': request.user.id,
                'delivery_method': request.data.get('delivery_method', 'Delivery'),
                'total_amount': cart.total_amount
            }
            order_serializer = OrderSerializer(data=order_data)
            order_serializer.is_valid(raise_exception=True)
            order = order_serializer.save()

            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variation=cart_item.variation,
                    quantity=cart_item.quantity,
                    price=cart_item.product.pricing.sale_price or cart_item.product.pricing.base_price,
                    vendor=cart_item.product.vendor
                )

            # Clear the cart
            cart.items.all().delete()

            # Here you would typically integrate with Paystack
            # payment_link = create_paystack_payment_link(order)
            # order.payment_reference = payment_link.reference
            # order.save()

            return Response({
                'order': order_serializer.data,
                # 'payment_link': payment_link.url
            }, status=status.HTTP_201_CREATED)
        except Cart.DoesNotExist:
            raise ValidationError('Cart not found')

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

    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        order = self.get_object()
        new_payment_status = request.data.get('payment_status')
        if new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
            order.payment_status = new_payment_status
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        raise ValidationError('Invalid payment status')