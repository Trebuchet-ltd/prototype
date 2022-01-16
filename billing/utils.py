import datetime

from django.contrib.auth.models import User

from home.models import Orders, TransactionDetails, OrderItem, Addresses, Purchase
from home.models import Product


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
    phone, name, address, pincode, user, gst = range(6)
    for key in data.keys():
        locals()[key] = data[key]

    customer, _ = User.objects.get_or_create(username=phone, first_name=name)

    address, _ = Addresses.objects.get_or_create(name=name, address=address, pincode=pincode, phone=phone, user=user,
                                                 state='kerala', gst=gst)

    return customer, address


def add_items(products, order=None, purchase=None):
    total = 0
    for product in products:
        if product:
            try:
                item = Product.objects.get(id=product["id"])
                weight = float(product['weight']) if "weight" in product else int(product['quantity'])
                cleaned = int(product['cleaned_status'])

                if cleaned and item.can_be_cleaned:
                    total += item.cleaned_price * weight
                else:

                    total += item.price * weight

                item.stock -= int(weight)
                item.save()

                quantity = 1
                if not item.type_of_quantity:
                    quantity, weight = weight, quantity

                if order:
                    OrderItem.objects.create(item=item, quantity=quantity, weight_variants=weight * 1000,
                                             is_cleaned=cleaned and item.can_be_cleaned, order=order)
                else:
                    OrderItem.objects.create(item=item, quantity=quantity, weight_variants=weight * 1000,
                                             is_cleaned=cleaned and item.can_be_cleaned, purchase=purchase)

            except Product.DoesNotExist:
                pass

        return total


def invoice_data_processor(invoice_post_data):
    customer, address = create_models(invoice_post_data)

    order = Orders.objects.create(user=customer, is_seen=True, status='d', address=address)
    transaction = TransactionDetails.objects.create(order=order, user=customer, payment_status='paid', )

    total = add_items(invoice_post_data['products'], order=order)

    for m in [transaction, order]:
        m.total = total
        m.save()

    return order


def product_data_processor(invoice_post_data):
    customer, address = create_models(invoice_post_data)
    purchase = Purchase.objects.create(user=customer, address=address)

    total = add_items(invoice_post_data['products'], purchase=purchase)

    purchase.total = total
    purchase.save()

    return purchase
