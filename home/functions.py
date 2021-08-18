"""
This file contains all the supporting functions needed for api view sets

"""
import logging

import requests
from .models import *
from django.contrib.gis.geos import GEOSGeometry
from requests.auth import HTTPBasicAuth
import datetime
import prototype.settings as settings
import hmac
import hashlib


def is_available_district(pincode):
    """
    This function find the district of corresponding pincode and check the  district is available for delivery
    returns true if available else false
    """
    logging.info("Checking the availability of  district ")
    pincode_obj = Pincodes.objects.filter(pincode=pincode).first()
    if pincode_obj:
        logging.info(f"requested pincode is found in database returning {pincode_obj.district.Available_status}")
        return pincode_obj.district.Available_status

    else:
        logging.info("requested pincode is not present in database")
        try:
            res = requests.get(f'https://api.postalpincode.in/pincode/{pincode}').json()
            try:
                district = res[0].get("PostOffice")[0].get("District")

                logging.info("district found from postal api ")
                # district obj contains the district if it is added to database else return null queryset
                district_obj = District.objects.filter(district_name=district).first()

                # this check whether the the district added to the database and it is available for delivery
                Pincodes.objects.create(pincode=pincode, district=district_obj)
                logging.info(f"Pincode {pincode} added to database successfully ")

                if not (district_obj and district_obj.Available_status):
                    return False
            except TypeError:
                logging.warning(f"{pincode} not found in post api ")
        except Exception as e:
            logging.warning(e)
        else:
            return False


def new_id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """ This function generate a random string  """

    return ''.join(random.choice(chars) for _ in range(size))


def create_new_unique_id():
    """ This function verify the uniqueness of an id for transaction """

    not_unique = True
    unique_id = new_id_generator()
    while not_unique:
        unique_id = new_id_generator()
        if not TransactionDetails.objects.filter(transaction_id=unique_id):
            not_unique = False
    return str(unique_id)


def create_temp_order(user, payment_id, date, time, address_obj, coupon_code='', points=0):
    """
    This will create an intermediate object of order and order items for storing the current cart items ans details
    """
    logging.info("Creating temporary order")
    if points:
        points = user.tokens.points
    else:
        points = 0

    coupon_obj = Coupon.objects.filter(code=coupon_code).first()
    if coupon_obj:
        order = TempOrder.objects.create(payment_id=payment_id, date=date, time=time,
                                         address_id=address_obj.id, coupon=coupon_obj, used_points=points,user=user)
        order.save()
    else:
        order = TempOrder.objects.create(payment_id=payment_id, date=date, time=time,
                                         address_id=address_obj.id,used_points=points,user=user)
        order.save()
    for item in user.cart.items.all():
        temp_item = TempItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                            weight_variants=item.weight_variants,
                                            is_cleaned=item.is_cleaned)
        temp_item.save()


def cancel_last_payment_links(user):
    logging.info("Cancelling last payment links")
    transaction_details = TransactionDetails.objects.filter(user=user, payment_status="created")
    key_secret = settings.razorpay_key_secret
    key_id = settings.razorpay_key_id
    for transaction in transaction_details:
        url = f'https://api.razorpay.com/v1/payment_links/{transaction.payment_id}/cancel'
        logging.info(f"canceling  {transaction.payment_id}")
        requests.post(url,
                      headers={'Content-type': 'application/json'},
                      auth=HTTPBasicAuth(key_id, key_secret))
        transaction.delete()


def get_payment_link(user, amount, address_obj):
    """
    This Function returns thr payment url for that particular checkout
    Returns a list with payment link and payment id created by razorpay
    """
    logging.info(f"{user} Requesting to get payment link ")
    key_secret = settings.razorpay_key_secret
    call_back_url = settings.webhook_call_back_url
    key_id = settings.razorpay_key_id
    cancel_last_payment_links(user)
    transaction_id = create_new_unique_id()
    transaction_details = TransactionDetails(transaction_id=transaction_id, user=user, total=amount)
    transaction_details.save()
    logging.info(f"created transaction details object for {user}")
    amount *= 100  # converting rupees to paisa
    try:
        url = 'https://api.razorpay.com/v1/payment_links'

        data = {
            "amount": amount,
            "currency": "INR",
            "callback_url": call_back_url,
            "callback_method": "get",
            'reference_id': transaction_id,
            "customer": {
                "contact": address_obj.phone,
                "email": user.email,
                "name": address_obj.name
            },
            "options": {
                "checkout": {
                    "name": "DreamEat",
                    "prefill": {
                        "email": user.email,
                        "contact": address_obj.phone
                    },
                    "readonly": {
                        "email": True,
                        "contact": True
                    }
                }
            }
        }
        x = requests.post(url,
                          json=data,
                          headers={'Content-type': 'application/json'},
                          auth=HTTPBasicAuth(key_id, key_secret))
        res = x.json()
        try:
            logging.info(f"Razorpay response object {res} ")
            transaction_details.payment_id = res.get("id")
            logging.info(f" Transaction id {res.get('id')} ,  status = {res.get('status')}")
            transaction_details.payment_status = res.get("status")
            transaction_details.save()
            logging.info(f"now created transaction details is {transaction_details}")
            payment_url = res.get('short_url')
            logging.info(f"payment url - {payment_url}")
            return [payment_url, transaction_details.payment_id]
        except KeyError:
            logging.warning(f"payment link creation failed ... {res} ")
            return [False, False]
    except Exception as e:
        logging.warning(e)
        return [False, False]


def is_valid_date(date_obj, time):
    """ This function check the user selected date and time is valid or not """
    logging.info("Validating the date")
    if (date_obj.date() - datetime.datetime.now().date()).days < 0:
        logging.info(f"date is a past date ")
        logging.info(date_obj.date)
        return False
    elif date_obj.date() == datetime.datetime.now().date():  # checking the date is today or not
        logging.info("the date is today")
        if time == "morning":  # if the date is today morning slot is not available
            logging.info("morning is not possible for today")
            return False
    logging.info("date validation completed successfully")
    return True


def is_out_of_stock(user):
    """ This function checks the stock availability of the product """
    logging.info(f"checking availability of stocks .... for user {user}")
    for item in user.cart.items.all():

        if item.item.type_of_quantity:
            reduction_in_stock = item.weight_variants * item.quantity / 1000
        else:
            reduction_in_stock = item.quantity
        if item.item.stock - reduction_in_stock < 0:
            logging.warning(f"{item.item} is out of stock")
            return item.item
    logging.info(f"checking completed all items are available for user {user} ")
    return False


def use_points(user, amount):
    logging.info(f"{user.username} requested to use points {user.tokens.points} ")
    return amount - user.tokens.points


def reduce_points(user):
    logging.info("user used points to checkout making points zero")
    user.tokens.points = 0
    user.tokens.save()


def add_points(token):
    """ Function to add points to user when first purchase occurs """
    logging.info("performing  adding points")
    purchase_done = Tokens.objects.get(invite_token=token).first_purchase_done
    if not purchase_done:
        invite_token = Tokens.objects.get(private_token=token)
        logging.info(f"user is invited by {invite_token.user.name}, adding 40 points... ")
        invite_token.total_points_yet += 40
        invite_token.points += 40
        logging.info("points adding completed")
        invite_token.save()
        return True

    return False


def is_valid_coupon(user, coupon_code, amount):
    """
    This function validates the specified coupon applicable or not
    Returns a list with first element will be the status (boolean) second element is the error if not valid
    Returns [True] if the coupon is valid
    """
    coupon_obj = Coupon.objects.filter(code=coupon_code.upper()).first()
    if not coupon_obj:
        return [False, "coupon code does not exist"]
    if not coupon_code:  # checks the coupon is existing one
        return [False, "coupon code does not exist"]
    order_with_same_cpn = Orders.objects.filter(user__exact=user, coupon=coupon_obj)
    if order_with_same_cpn:
        return [False, "coupon code does not exist"]
    if coupon_obj.expired:  # check the coupon expired or not
        return [False, "coupon code does not exist"]
    if coupon_obj.user_specific_status:  # checks the coupon is user specific or not
        if coupon_obj.specific_user != user:  # check the specific user is not the requested user
            return [False, "coupon code does not exist"]
    if coupon_obj.minimum_price > amount:  # checks the minimum price condition
        return [False, f"This coupon is applicable to the amount greater than {coupon_obj.minimum_price} "]

    return [True]


def apply_coupon(user, coupon_code, amount):
    """
    This function apply the coupon code and
    """
    logging.info(f"{user} Requested to apply the coupon  {coupon_code}")
    coupon_obj = Coupon.objects.filter(code=coupon_code.upper()).first()
    if coupon_obj:
        logging.info("Found coupon corresponding to requested coupon ")
        if is_valid_coupon(user, coupon_code, amount)[0]:
            logging.info("Requested coupon is a valid coupon ")
            logging.info(f"amount before applying coupon is {amount} ")
            if coupon_obj.discount_type == 0:  # constant type coupon
                amount -= coupon_obj.discount_value
                logging.info(f"amount after applying coupon is {amount} ")
            else:  # percentage type
                amount *= (100 - coupon_obj.discount_value) / 100
                logging.info(f"amount after applying coupon is {amount} ")

    return amount


def total_amount(user, address_obj, coupon_code='', points=False, without_coupon=False):
    """
    This function returns the total amount of the cart items of the user
    Return 0 if the amount is zero
    return amount + delivery charge if amount less than 500
    return amount if amount more than 500
    If any coupon code is present it will apply before adding the delivery charge if any
    """
    logging.info(f"calculating total amount for user {user},address-obj ={address_obj}  coupon-{coupon_code} points-{points}")
    cart = user.cart
    amount = 0

    for item in cart.items.all():
        if item.quantity > 0:
            if item.is_cleaned:
                amount += item.quantity * item.item.cleaned_price * item.weight_variants / 1000
            else:
                if item.item.type_of_quantity:
                    amount += item.quantity * item.item.price * item.weight_variants / 1000
                else:
                    amount += item.quantity * item.item.price
        elif item.quantity < 0:
            if item.is_cleaned:
                amount += -item.quantity * item.item.cleaned_price * item.weight_variants / 1000
            else:
                if item.item.type_of_quantity:
                    amount -= item.quantity * item.item.price * item.weight_variants / 1000
                else:
                    amount -= item.quantity * item.item.price
    logging.info(f"Amount calculated before adding delivery charge is {amount}")
    if amount <= 0:  # if the amount is 0 then it should not add the delivery charge
        return 0

    if not without_coupon:
        if coupon_code:
            amount = apply_coupon(user, coupon_code, amount)

    if amount < 500:  # if amount lee than 500 it will apply the coupon if any and add delivery charge
        logging.info(f"Adding delivery charge .... for amount {amount} ")
        amount += address_obj.delivery_charge
    if points:
        amount = use_points(user, amount)
        logging.info(f"applied coupon ! Now the amount is {amount} ")
    return amount


def verify_signature(request):
    logging.info("Signature verification taking place")
    try:
        signature_payload = request.GET['razorpay_payment_link_id'] + '|' +\
            request.GET['razorpay_payment_link_reference_id']+ '|' +\
            request.GET['razorpay_payment_link_status'] + '|' +\
            request.GET['razorpay_payment_id']
        signature_payload = bytes(signature_payload, 'utf-8')
        byte_key = bytes(settings.razorpay_key_secret, 'utf-8')
        generated_signature = hmac.new(byte_key, signature_payload, hashlib.sha256).hexdigest()
        if generated_signature == request.GET["razorpay_signature"]:
            logging.info("Signature verification successfully completed")
            return True
        else:
            logging.warning("signature verification failed")
            return False
    except ValueError:
        logging.warning("signature verification failed value error")
        return False
    except Exception as e:
        logging.warning("signature verification failed")
        logging.warning(e)


def create_order_items(cart, temp_items, order):
    logging.info("creating order items")
    for item in temp_items.all():
        order_item = OrderItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                              weight_variants=item.weight_variants,
                                              is_cleaned=item.is_cleaned)
        order_item.save()
        if item.item.type_of_quantity:
            reduction_in_stock = item.weight_variants * item.quantity / 1000
        else:
            reduction_in_stock = item.quantity
        item.item.stock -= reduction_in_stock
        item.item.save()
        CartItem.objects.filter(item=item.item, weight_variants=item.weight_variants,
                                is_cleaned=item.is_cleaned).delete()
        item.delete()

    cart.total = 0
    cart.save()


def distance_between(loc1, loc2):
    pnt1 = GEOSGeometry(f"POINT ({loc1[1]} {loc1[0]})", srid=4326)
    pnt2 = GEOSGeometry(f"POINT ({loc2[1]} {loc2[0]})", srid=4326)
    distance = pnt1.distance(pnt2) * 100
    return distance*1.45


def get_delivery_charge(location):
    distance = distance_between(settings.location, [location[0], location[1]])
    if distance <= 10:
        return 30
    else:
        return 60
