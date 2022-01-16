import datetime

from django.contrib.auth.models import User

from billing.models import BillingProduct
from home.models import Orders, TransactionDetails, OrderItem, Addresses, Purchase
from home.models import Product
from organisation.models import Organisation


def invoice_data_validator(invoice_data):
    try:
        int(invoice_data['invoice-number'])
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


def create_models(data):
    customer, _ = User.objects.get_or_create(username=data["phone"], first_name=data["name"])
    address, _ = Addresses.objects.get_or_create(
        name=data["name"], address=data["address"], pincode=data["pincode"],
        phone=data["phone"], user=customer, state='kerala', gst=data["gst"]
    )

    return customer, address


def add_items(products, order=None, purchase=None):
    total = 0
    for product in products:
        try:
            item = BillingProduct.objects.get(id=product["id"])
            quantity = float(product['quantity'])
            cleaned = bool(product['cleaned_status'])
            price = float(product["price"] or (item.cleaned_price if cleaned and item.can_be_cleaned else item.price))

            total += price * quantity

            item.stock -= quantity
            item.save()

            if order:
                OrderItem.objects.create(item=item, quantity=quantity, is_cleaned=cleaned and item.can_be_cleaned,
                                         order=order, price=price)
            else:
                OrderItem.objects.create(item=item, quantity=quantity, is_cleaned=cleaned and item.can_be_cleaned,
                                         purchase=purchase, price=price)

        except Product.DoesNotExist:
            pass

    return total


def invoice_data_processor(invoice_post_data, org: Organisation):
    customer, address = create_models(invoice_post_data)

    if invoice_post_data["type"] == "c":
        org.c_invoice_count += 1
        count = org.c_invoice_count
    else:
        org.b_invoice_count += 1
        count = org.b_invoice_count

    org.save()

    order = Orders.objects.create(user=customer, is_seen=True, status='d', address=address, organisation=org,
                                  invoice_number=count)
    transaction = TransactionDetails.objects.create(order=order, user=customer, payment_status='paid')

    total = add_items(invoice_post_data['products'], order=order)

    for m in [transaction, order]:
        m.total = total
        m.save()

    return order


def product_data_processor(invoice_post_data, org):
    customer, address = create_models(invoice_post_data)
    purchase = Purchase.objects.create(user=customer, address=address, organisation=org)

    total = add_items(invoice_post_data['products'], purchase=purchase)

    purchase.total = total
    purchase.save()

    return purchase
