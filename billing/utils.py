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

    customer_name = invoice_post_data['name']
    customer_address = invoice_post_data['address']
    customer_phone = invoice_post_data['phone']
    customer_pincode = invoice_post_data['pincode']

    user, _ = User.objects.get_or_create(username=invoice_post_data['phone'],
                                         first_name=invoice_post_data['name'], )
    address, _ = Addresses.objects.get_or_create(name=customer_name, address=customer_address, pincode=customer_pincode,
                                                 phone=customer_phone, user=user, state='kerala')
    order = Orders.objects.create(user=user, is_seen=True, status='d', address=address)
    transaction = TransactionDetails.objects.create(order=order, user=user, payment_status='paid', )

    invoice_post_data = dict(invoice_post_data)

    for product in invoice_post_data['products']:
        amount = 0
        if product:
            try:
                item = Product.objects.get(id=product["id"])
                weight = float(product['weight'])
                quantity = int(product['quantity'])
                cleaned = int(product['cleaned_status'])
                print(f"{cleaned = }")
                if cleaned and item.can_be_cleaned:

                    amount += item.cleaned_price * weight
                else:
                    if item.type_of_quantity:

                        amount += quantity * item.price * weight
                    else:
                        amount += quantity * item.price

                order.total += amount
                transaction.total += amount
                item.stock -= int(weight * quantity)
                item.save()
                transaction.save()
                order.save()
                print(f"{amount = }")
                OrderItem.objects.create(item=item, quantity=quantity, weight_variants=weight*1000, is_cleaned=cleaned and item.can_be_cleaned,
                                         order=order)
            except Product.DoesNotExist:
                pass

    return order
