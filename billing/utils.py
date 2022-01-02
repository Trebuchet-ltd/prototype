import datetime
import json

from django.contrib.auth.models import User
from django.db.models import Sum

from home.models import Orders, TransactionDetails, OrderItem, Addresses
from home.models import Product


def invoice_data_validator(invoice_data):
    # Validate Invoice Info ----------

    # invoice-number
    try:
        invoice_number = int(invoice_data['invoice-number'])
    except:
        print("Error: Incorrect Invoice Number")
        return "Error: Incorrect Invoice Number"

    # invoice date
    try:
        date_text = invoice_data['invoice-date']
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except:
        print("Error: Incorrect Invoice Date")
        return "Error: Incorrect Invoice Date"


def invoice_data_processor(invoice_post_data):
    print(invoice_post_data)
    processed_invoice_data = {}

    processed_invoice_data['invoice_number'] = invoice_post_data['invoice-number']
    processed_invoice_data['invoice_date'] = invoice_post_data['invoice-date']

    customer_name = invoice_post_data['customer-name']
    customer_address = invoice_post_data['customer-address']
    customer_phone = invoice_post_data['customer-phone']
    # customer_pincode = invoice_post_data['pincode']
    user, _ = User.objects.get_or_create(username=invoice_post_data['customer-phone'],
                                         first_name=invoice_post_data['customer-name'], )
    address, _ = Addresses.objects.get_or_create(name=customer_name, address=customer_address, pincode=679357,
                                                 phone=customer_phone, user=user, state='kerala')
    order = Orders.objects.create(user=user, is_seen=True, status='d', address=address)
    transaction = TransactionDetails.objects.create(order=order, user=user, payment_status='paid', )

    if 'igstcheck' in invoice_post_data:
        processed_invoice_data['igstcheck'] = True
    else:
        processed_invoice_data['igstcheck'] = False

    invoice_post_data = dict(invoice_post_data)

    for idx, product in enumerate(invoice_post_data['invoice-product']):
        if product:
            try:
                item = Product.objects.get(title=product)
                weight = float(invoice_post_data['invoice-unit'][idx])
                quantity = int(invoice_post_data['invoice-qty'][idx])
                amt_with_tax = item.price * weight * (1 + item.product_gst_percentage / 100)
                transaction.total += amt_with_tax * (1 - item.discount / 100)
                transaction.invoice_amt_without_gst = item.price * weight * (1 - item.discount / 100)
                item.stock -= int(weight * quantity/1000)
                item.save()
                is_cleaned = True
                OrderItem.objects.create(item=item, quantity=quantity, weight_variants=weight, is_cleaned=is_cleaned,
                                         order=order)
            except Product.DoesNotExist:
                pass
    return order
