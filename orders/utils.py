import requests
from django.conf import settings

# Your Paystack secret key from the environment or settings
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY

def create_paystack_payment_link(order):
    """
    Creates a Paystack payment link for a given order.
    :param order: The order object for which to generate a payment link
    :return: A dict containing payment authorization URL and reference
    """
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }

    # Data for the payment link
    data = {
        'email': order.customer.email,  # Customer's email
        'amount': int(order.total_amount * 100),  # Paystack accepts amounts in kobo
        'reference': f"ORD-{order.id}",  # Unique reference
        'callback_url': 'https://yourdomain.com/payment/callback/',  # Replace with your actual callback URL
        'metadata': {
            'order_id': str(order.id),
            'custom_fields': [
                {
                    'display_name': 'Order ID',
                    'variable_name': 'order_id',
                    'value': str(order.id)
                },
                {
                    'display_name': 'Customer Name',
                    'variable_name': 'customer_name',
                    'value': order.customer.name
                }
            ]
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data['status']:
            # Return the payment link and reference if successful
            return {
                'authorization_url': response_data['data']['authorization_url'],
                'reference': response_data['data']['reference']
            }
        else:
            # Handle Paystack error
            raise Exception(f"Paystack error: {response_data['message']}")
    
    except requests.RequestException as e:
        # Handle request errors
        raise Exception(f"Network error while contacting Paystack: {str(e)}")
