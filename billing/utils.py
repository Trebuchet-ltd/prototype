import datetime
import json

from django.contrib.auth.models import User
from django.db.models import Sum

from home.models import Orders, TransactionDetails, OrderItem, Addresses
from .models import Book
from .models import BookLog
from .models import Inventory
from .models import InventoryLog
from .models import Product


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
                print(f"{invoice_post_data = } {idx = }")
                item = Product.objects.get(name=product["name"])
                weight = float(invoice_post_data['invoice-unit'][idx])
                quantity = int(invoice_post_data['invoice-qty'][idx])
                amt_with_tax = item.price * weight * (1 + item.product_gst_percentage / 100)
                transaction.total += amt_with_tax * (1 - item.discount / 100)
                transaction.invoice_amt_without_gst = item.price * weight * (1 - item.discount / 100)

                is_cleaned = True
                OrderItem.objects.create(item=item, quantity=quantity, weight_variants=weight, is_cleaned=is_cleaned,
                                         order=order)
            except Product.DoesNotExist:
                pass

    print(processed_invoice_data)
    return order


def update_products_from_invoice(invoice_data_processed, request):
    for item in invoice_data_processed['items']:
        new_product = False
        if Product.objects.filter(user=request.user,
                                  product_name=item['invoice_product'],
                                  product_hsn=item['invoice_hsn'],
                                  product_unit=item['invoice_unit'],
                                  product_gst_percentage=item['invoice_gst_percentage']).exists():
            product = Product.objects.get(user=request.user,
                                          product_name=item['invoice_product'],
                                          product_hsn=item['invoice_hsn'],
                                          product_unit=item['invoice_unit'],
                                          product_gst_percentage=item['invoice_gst_percentage'])
        else:
            new_product = True
            product = Product(user=request.user,
                              product_name=item['invoice_product'],
                              product_hsn=item['invoice_hsn'],
                              product_unit=item['invoice_unit'],
                              product_gst_percentage=item['invoice_gst_percentage'])
        product.product_rate_with_gst = item['invoice_rate_with_gst']
        product.save()

        if new_product:
            create_inventory(product)


#  ================== Inventory methods ====================

def create_inventory(product):
    if not Inventory.objects.filter(user=product.user, product=product).exists():
        new_inventory = Inventory(user=product.user, product=product)
        new_inventory.save()


def update_inventory(invoice, request):
    invoice_data = json.loads(invoice.invoice_json)
    for item in invoice_data['items']:
        product = Product.objects.get(user=request.user,
                                      product_name=item['invoice_product'],
                                      product_hsn=item['invoice_hsn'],
                                      product_unit=item['invoice_unit'],
                                      product_gst_percentage=item['invoice_gst_percentage'])
        inventory = Inventory.objects.get(user=product.user, product=product)
        change = int(item['invoice_qty']) * (-1)
        inventory_log = InventoryLog(user=product.user,
                                     product=product,
                                     date=datetime.datetime.now(),
                                     change=change,
                                     change_type=4,
                                     associated_invoice=invoice,
                                     description="Sale - Auto Deduct")
        inventory_log.save()
        inventory.current_stock += change
        inventory.last_log = inventory_log
        inventory.save()


def remove_inventory_entries_for_invoice(invoice, user):
    inventory_logs = InventoryLog.objects.filter(user=user,
                                                 associated_invoice=invoice)
    for inventory_log in inventory_logs:
        inventory_product = inventory_log.product
        inventory_log.delete()
        # update the inventory total
        inventory_obj = Inventory.objects.get(user=user, product=inventory_product)
        recalculate_inventory_total(inventory_obj, user)


def recalculate_inventory_total(inventory_obj, user):
    new_total = InventoryLog.objects.filter(user=user, product=inventory_obj.product).aggregate(Sum('change'))[
        'change__sum']
    if not new_total:
        new_total = 0
    inventory_obj.current_stock = new_total
    inventory_obj.save()


# ================ Book methods ===========================

def add_customer_book(customer):
    # check if customer already exists
    if Book.objects.filter(user=customer.user, customer=customer).exists():
        return
    book = Book(user=customer.user,
                customer=customer)
    book.save()


def auto_deduct_book_from_invoice(invoice):
    invoice_data = json.loads(invoice.invoice_json)

    book = Book.objects.get(user=invoice.user, customer=invoice.invoice_customer)

    book_log = BookLog(parent_book=book,
                       date=invoice.invoice_date,
                       change_type=1,
                       change=(-1.0) * float(invoice_data['invoice_total_amt_with_gst']),
                       associated_invoice=invoice,
                       description="Purchase - Auto Deduct")

    book_log.save()

    book.current_balance = book.current_balance + book_log.change
    book.last_log = book_log
    book.save()
