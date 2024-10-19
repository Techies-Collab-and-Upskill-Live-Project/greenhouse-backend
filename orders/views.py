from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import *
from .serializers import *
import requests
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import hmac
import hashlib
from django.http import HttpResponse, JsonResponse


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @action(detail=True, methods=['post'], serializer_class=CartItemSerializer)
    def add_item(self, request, pk=None):
        cart = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product_id']
        variation_id = serializer.validated_data.get('variation_id')
        quantity = serializer.validated_data['quantity']

        product = get_object_or_404(Product, id=product_id)
        variation = get_object_or_404(ProductVariation, id=variation_id) if variation_id else None

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variation=variation,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        cart_item_serializer = CartItemSerializer(cart_item)
        return Response(cart_item_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], serializer_class=CartSerializer)
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart_item_id = serializer.validated_data['cart_item_id']
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=cart)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['get'])
    def get_total(self, request, pk=None):
        cart = self.get_object()
        return Response({'total': cart.total_amount}, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

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
            'shipping_method': request.data.get('shipping_method', 'Door Delivery'),
            'total_amount': cart.total_amount,
            'subtotal': cart.subtotal,
            'vat_amount': cart.vat_amount,
            'shipping_rate': cart.shipping_rate,
            'status': 'Pending',
            'shipping_address': request.data.get('shipping_address', '')
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

        OrderStatusUpdate.objects.create(order=order, status='Pending', completed=True)

        cart.items.all().delete()

        payment_link = self.create_paystack_payment_link(order, request)
        order.payment_reference = payment_link['reference']
        order.save()

        return Response({
            'order': order_serializer.data,
            'payment_link': payment_link['authorization_url']
        }, status=status.HTTP_201_CREATED)

    def create_paystack_payment_link(self, order, request):
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        callback_url = request.build_absolute_uri(reverse('paystack_webhook'))  # Pointing to the webhook
        data = {
            'amount': int(order.total_amount * 100),  # Amount in kobo
            'email': request.user.email,
            'reference': f'order_{order.id}',
            'callback_url': callback_url,
            'channels': ['card', 'bank', 'ussd', 'qr', 'mobile_money', 'bank_transfer'],
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['data']
        raise ValidationError('Failed to create payment link')


    
@csrf_exempt
@require_POST
def paystack_webhook(request):
    paystack_secret = settings.PAYSTACK_SECRET_KEY
    payload = request.body
    signature = request.headers.get('X-Paystack-Signature')

    if not signature:
        return HttpResponse(status=400)

    # Verify the webhook signature
    expected_signature = hmac.new(paystack_secret.encode('utf-8'), payload, hashlib.sha512).hexdigest()
    if signature != expected_signature:
        return HttpResponse(status=400)

    # Parse the payload
    try:
        payload = json.loads(payload)
        event = payload['event']
        data = payload['data']
    except (json.JSONDecodeError, KeyError):
        return HttpResponse(status=400)

    # Retrieve the payment details
    reference = data.get('reference')
    amount = data.get('amount')
    payment_method = data.get('channel')

    try:
        order = Order.objects.get(payment_reference=reference)
    except Order.DoesNotExist:
        return HttpResponse(status=404)

    # Handle different Paystack events
    if event == 'charge.success':
        if data.get('status') == 'success':
            # Mark order as paid
            order.status = 'Processing'
            order.payment_status = 'Paid'
            order.payment_method = payment_method
            order.save()
            OrderStatusUpdate.objects.create(order=order, status='Processing', completed=True)
    
    elif event == 'charge.failed':
        # Mark order as failed
        order.payment_status = 'Failed'
        order.status = 'Cancelled'
        order.payment_method = payment_method
        order.save()
        OrderStatusUpdate.objects.create(order=order, status='Cancelled', completed=True)
    
    # Handle other events if needed (e.g., 'charge.dispute', etc.)
    elif event == 'charge.dispute.create':
        # Log the dispute and potentially flag the order for review
        order.status = 'Disputed'
        order.save()
        OrderStatusUpdate.objects.create(order=order, status='Disputed', completed=False)
    
    # Add more event handlers as needed

    return HttpResponse(status=200)



# @csrf_exempt
# def paystack_webhook(request):
#     # Only allow POST requests
#     if request.method == 'POST':
#         # Retrieve the event payload
#         payload = json.loads(request.body)
#         event = payload.get('event')
#         data = payload.get('data', {})
        
#         # Retrieve the payment details
#         reference = payload['data']['reference']
#         amount = payload['data']['amount']
#         payment_method = payload['data']['channel']
        
#         try:
#             order = Order.objects.get(payment_reference=reference)
#         except Order.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=400)

#         # Handle different Paystack events
#         if event == 'charge.success':
#             # Verify the payment status
#             if data.get('status') == 'success':
#                 # Mark order as paid
#                 order.status = 'Processing'
#                 order.payment_status = 'Paid'
#                 order.payment_method = payment_method
#                 order.save()
#                 OrderStatusUpdate.objects.create(order=order, status='Processing', completed=True)
#                 return JsonResponse({'status': 'success', 'message': 'Payment successful'}, status=200)
        
#         elif event == 'charge.failed':
#             # Mark order as failed
#             order.payment_status = 'Failed'
#             order.status = 'Cancelled'
#             order.payment_method = payment_method
#             order.save()
#             OrderStatusUpdate.objects.create(order=order, status='Pending', completed=False)
#             return JsonResponse({'status': 'error', 'message': 'Payment failed'}, status=200)
        
#         # Handle other events if needed (e.g., 'charge.dispute', etc.)

#         return JsonResponse({'status': 'success', 'message': 'Event processed'}, status=200)

#     return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
