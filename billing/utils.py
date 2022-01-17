import datetime
from typing import List

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


def render_bill(body, qty, total, seller, customer, date, invoice_id, gst_subtotal):
    return f"""
GST IN: {seller['gst']:<{55}}Phone : {seller['phone']:>{12}}
{seller['name']:^{83}}
{seller['address']:^{83}}
{"Tax Invoice":^{83}}

    To                                           Invoice Number : {invoice_id}
                                                 Invoice Date : {date}
        {customer['name']}
        {customer['address']}
        {customer['phone']}
        {customer['gst']}
        
+---------------------------------------------------------------------------------+
| Sl |  Code  |             Product             |  Qty  | Price | GST | Net Price |
+---------------------------------------------------------------------------------+
{body}
+---------------------------------------------------------------------------------+
|                                                           Sub Total:            |
+---------------------------------------------------------------------------------+
{gst_subtotal}
+---------------------------------------------------------------------------------+
|             Total                             |{qty:>{7}}|{total:>{25}}|
+---------------------------------------------------------------------------------+
    """


def create_bill(invoice: Orders, items: List[OrderItem], invoice_id):
    rows = []
    qty, total, gst = 0, 0, 0

    for sl, i in enumerate(items):
        ii = i.item

        net = i.price * i.quantity
        title = ii.title
        line2 = False

        qty += i.quantity
        total += net
        gst += ii.gst_percent * net / (100.0 + ii.gst_percent)

        if len(title) > 33:
            line1 = title[:32] + '-'
            line2 = title[32:]
        else:
            line1 = title
        rows.append(
            f"|{sl + 1:>{4}}|{ii.code:<{8}}|{line1:<{33}}|{i.quantity:>{7}}|{i.price:>{7}}|{ii.gst_percent:>{4}}%|{net:>{11}}|")
        if line2:
            rows.append(f"|{'':>{4}}|{'':<{8}}|{line2:<{33}}|{'':>{7}}|{'':<{7}}|{'':<{5}}|{'':>{11}}|")

    seller = {
        "name": invoice.organisation.name,
        "phone": invoice.organisation.address.phone,
        "gst": invoice.organisation.gst_no,
        "address": invoice.organisation.address.address
    }

    customer = {
        "name": invoice.address.name,
        "phone": invoice.address.phone,
        "address": invoice.address.address,
        "gst": invoice.address.gst
    }

    if 670001 < int(invoice.address.pincode) < 695615:
        g = str(round(gst / 2, 1))
        gst_s = f"|{'':<{62}}CGST : {g:<{12}}|"
        gst_s += f"\n|{'':<{62}}SGST : {g:<{12}}|"
    else:
        g = str(round(gst, 1))
        gst_s = f"|{'':<{62}}IGST : {g:<{12}}|"

    return render_bill("\n".join(rows), qty, total, seller, customer, invoice.date, invoice_id, gst_s)
