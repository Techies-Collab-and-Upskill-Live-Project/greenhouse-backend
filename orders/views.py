from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import *
from .serializers import *
from decimal import Decimal
import requests
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import hmac
from uuid import UUID
import hashlib
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure user is authenticated before accessing
        if not self.request.user.is_authenticated:
            return Cart.objects.none()
        return Cart.objects.filter(customer=self.request.user)

    def get_object(self):
        # Get or create cart for the user
        cart, created = Cart.objects.get_or_create(
            customer=self.request.user,
            defaults={} # Add any default fields your Cart model needs
        )
        return cart

    @action(detail=False, methods=['post'], serializer_class=CartItemSerializer)
    def add_item(self, request):
        try:
            cart = self.get_object()
            serializer = self.get_serializer(data=request.data)
            
            # Explicitly validate and handle validation errors
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Safely get values with proper error handling
            product_id = serializer.validated_data.get('product_id')
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            variation_id = serializer.validated_data.get('variation_id')
            quantity = serializer.validated_data.get('quantity', 1)  # Default to 1 if not specified
            
            # Validate product exists
            try:
                product = get_object_or_404(Product, id=product_id)
            except ValidationError:
                return Response(
                    {'error': 'Invalid product_id format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate variation if provided
            variation = None
            if variation_id:
                try:
                    variation = get_object_or_404(ProductVariation, id=variation_id)
                    # Verify variation belongs to product
                    if variation.product_id != product.id:
                        return Response(
                            {'error': 'Variation does not belong to the specified product'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except ValidationError:
                    return Response(
                        {'error': 'Invalid variation_id format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Get or create cart item with error handling
            try:
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
                return Response(
                    cart_item_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], serializer_class=RemoveCartItemSerializer)
    def remove_item(self, request):
        try:
            cart = self.get_object()
            serializer = self.get_serializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                # Ensure the cart item exists and belongs to the user's cart
                cart_item = CartItem.objects.get(
                    id=serializer.validated_data['cart_item_id'],
                    cart=cart
                )
            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Cart item not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Handle quantity-based removal if specified
            quantity_to_remove = serializer.validated_data.get('quantity')
            
            if quantity_to_remove:
                if quantity_to_remove < cart_item.quantity:
                    cart_item.quantity -= quantity_to_remove
                    cart_item.save()
                    return Response(
                        CartItemSerializer(cart_item).data,
                        status=status.HTTP_200_OK
                    )
            
            # Delete the cart item
            cart_item.delete()
            
            return Response(
                {'message': 'Item removed from cart'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=True, methods=['get'])
    def get_total(self, request, pk=None):
        cart = self.get_object()
        return Response({'total': cart.total_amount}, status=status.HTTP_200_OK)


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    def create_paystack_payment_link(self, order, request):
        """Create Paystack payment link with proper UUID handling"""
        try:
            url = 'https://api.paystack.co/transaction/initialize'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            callback_url = request.build_absolute_uri(
                reverse('paystack_webhook')
            )
            
            # Convert all amounts to kobo (smallest currency unit)
            amount_in_kobo = int(float(order.total_amount) * 100)
            
            payload = {
                'amount': amount_in_kobo,
                'email': request.user.email,
                'reference': f'order_{str(order.id)}',
                'callback_url': callback_url,
                'channels': ['card', 'bank', 'ussd', 'bank_transfer'],
                'metadata': {
                    'order_id': str(order.id),
                    'customer_id': str(request.user.id),
                    'customer_email': request.user.email
                }
            }

            # Use the custom encoder for the request
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload, cls=UUIDEncoder),
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Paystack API error: {response.text}")
                raise ValidationError(f"Payment service error: {response.status_code}")

            response_data = response.json()
            
            if not response_data.get('status'):
                logger.error(f"Paystack API returned error: {response_data.get('message')}")
                raise ValidationError(response_data.get('message', 'Payment initialization failed'))

            return response_data['data']

        except requests.RequestException as e:
            logger.error(f"Paystack API request error: {str(e)}")
            raise ValidationError('Payment service is currently unavailable')
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Paystack: {str(e)}")
            raise ValidationError('Invalid response from payment service')
        
        except Exception as e:
            logger.error(f"Unexpected error in payment link creation: {str(e)}")
            raise ValidationError('Failed to create payment link')

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_from_cart(self, request):
        """Create an order from the user's cart with improved error handling"""
        try:
            # Get the user's cart
            cart = get_object_or_404(Cart, customer=request.user)
            
            # Validate cart has items
            if not cart.items.exists():
                return Response(
                    {'error': 'Cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate required fields
            shipping_address = request.data.get('shipping_address')
            if not shipping_address:
                return Response(
                    {'error': 'Shipping address is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate order amounts
            subtotal = sum(
                item.quantity * (item.product.pricing.sale_price or item.product.pricing.base_price)
                for item in cart.items.all()
            )
            
            # Get shipping method and rate
            shipping_method = request.data.get('shipping_method', 'Door Delivery')
            shipping_rate = Decimal(request.data.get('shipping_rate', '0.00'))
            
            # Calculate VAT
            vat_percentage = Decimal(request.data.get('vat_percentage', '7.50'))
            vat_amount = (subtotal * vat_percentage) / Decimal('100.00')
            
            # Calculate total
            total_amount = subtotal + vat_amount + shipping_rate

            # Create order
            order_data = {
                'customer': request.user,
                'shipping_method': shipping_method,
                'shipping_address': shipping_address,
                'total_amount': total_amount,
                'subtotal': subtotal,
                'vat_percentage': vat_percentage,
                'vat_amount': vat_amount,
                'shipping_rate': shipping_rate,
                'status': 'Pending',
                'payment_status': 'Pending'
            }

            order = Order.objects.create(**order_data)

            # Create order items
            order_items = []
            for cart_item in cart.items.all():
                price = cart_item.product.pricing.sale_price or cart_item.product.pricing.base_price
                order_items.append(
                    OrderItem(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=price,
                        vendor=cart_item.product.vendor if hasattr(cart_item.product, 'vendor') else None
                    )
                )
            
            # Bulk create order items
            OrderItem.objects.bulk_create(order_items)

            # Create initial status update
            OrderStatusUpdate.objects.create(
                order=order,
                status='Pending',
                completed=True
            )

            try:
                # Create payment link with proper error handling
                payment_data = self.create_paystack_payment_link(order, request)
                
                if not payment_data or 'authorization_url' not in payment_data:
                    raise ValidationError('Invalid payment data received')

                order.payment_reference = payment_data['reference']
                order.save()

                return Response({
                    'order': OrderSerializer(order).data,
                    'payment_link': payment_data['authorization_url']
                }, status=status.HTTP_201_CREATED)

            except ValidationError as e:
                logger.error(f"Payment validation error: {str(e)}")
                order.delete()
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            except Exception as e:
                logger.error(f"Payment link creation failed: {str(e)}")
                order.delete()
                return Response(
                    {'error': 'Failed to setup payment. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}")
            return Response(
                {'error': 'Failed to create order. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    
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
