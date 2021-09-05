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

logger = logging.getLogger("home")


def is_available_district(pincode):
    """
    This function find the district of corresponding pincode and check the  district is available for delivery
    returns true if available else false
    """
    logger.info("Checking the availability of  district ")
    pincode_obj = Pincodes.objects.filter(pincode=pincode).first()
    if pincode_obj:
        logger.info(f"requested pincode is found in database returning {pincode_obj.district.Available_status}")
        return pincode_obj.district.Available_status

    else:
        logger.info("requested pincode is not present in database")
        try:
            res = requests.get(f'https://api.postalpincode.in/pincode/{pincode}').json()
            try:
                district = res[0].get("PostOffice")[0].get("District")

                logger.info("district found from postal api ")
                # district obj contains the district if it is added to database else return null queryset
                district_obj = District.objects.filter(district_name=district).first()

                # this check whether the the district added to the database and it is available for delivery
                if district_obj:
                    Pincodes.objects.create(pincode=pincode, district=district_obj)
                    logger.info(f"Pincode {pincode} added to database successfully ")
                    return district_obj.Available_status
                else:
                    logger.info(f"district not found in database. district name is {district}")
                    return False
            except TypeError:
                logger.warning(f"{pincode} not found in post api ")
                return False
        except Exception as e:
            logger.warning(e)
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


def create_temp_order(user, payment_id, date, time, address_obj, coupon_code='', points=False):
    """
    This will create an intermediate object of order and order items for storing the current cart items ans details
    """
    logger.info("Creating temporary order")
    if points:

        points = user.tokens.points
        logger.info(f"Adding {points} -points to temp order")
    else:
        points = 0

    coupon_obj = Coupon.objects.filter(code__iexact=coupon_code).first()
    logger.info(f"coupon object = {coupon_obj}")
    if coupon_obj:
        logger.info("coupon object found adding to temporary order")
        order = TempOrder.objects.create(payment_id=payment_id, date=date, time=time,
                                         address_id=address_obj.id, coupon=coupon_obj,
                                         used_points=points, user=user, )
        logger.info(order)
        order.save()
    else:
        order = TempOrder.objects.create(payment_id=payment_id, date=date, time=time,
                                         address_id=address_obj.id, used_points=points,
                                         user=user, )
        order.save()
    for item in user.cart.items.all():
        logger.info(
            f"Adding {item.item}-{item.quantity} -{item.weight_variants} -variant cleaned status {item.is_cleaned} ")
        temp_item = TempItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                            weight_variants=item.weight_variants,
                                            is_cleaned=item.is_cleaned)

        temp_item.save()
    logger.info(f"created temporary order {order}")


def cancel_last_payment_links(user):
    logger.info("Cancelling last payment links")
    transaction_details = TransactionDetails.objects.filter(user=user, payment_status="created")
    key_secret = settings.razorpay_key_secret
    key_id = settings.razorpay_key_id
    for transaction in transaction_details:
        url = f'https://api.razorpay.com/v1/payment_links/{transaction.payment_id}/cancel'
        logger.info(f"canceling  {transaction.payment_id}")
        requests.post(url,
                      headers={'Content-type': 'application/json'},
                      auth=HTTPBasicAuth(key_id, key_secret))
        transaction.delete()


def get_payment_link(user, amount, amount_saved, address_obj):
    """
    This Function returns thr payment url for that particular checkout
    Returns a list with payment link and payment id created by razorpay
    """
    logger.info(f"{user} Requesting to get payment link ")
    key_secret = settings.razorpay_key_secret
    call_back_url = settings.webhook_call_back_url
    key_id = settings.razorpay_key_id
    cancel_last_payment_links(user)
    transaction_id = create_new_unique_id()
    transaction_details = TransactionDetails(transaction_id=transaction_id, user=user,
                                             total=amount, amount_saved=amount_saved)
    transaction_details.save()
    logger.info(f"created transaction details object for {user}")
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
            logger.info(f"Razorpay response object {res} ")
            transaction_details.payment_id = res.get("id")
            logger.info(f" Transaction id {res.get('id')} ,  status = {res.get('status')}")
            transaction_details.payment_status = res.get("status")
            transaction_details.save()
            logger.info(f"now created transaction details is {transaction_details}")
            payment_url = res.get('short_url')
            logger.info(f"payment url - {payment_url}")
            return [payment_url, transaction_details.payment_id]
        except KeyError:
            logger.warning(f"payment link creation failed ... {res} ")
            return [False, False]
    except Exception as e:
        logger.warning(e)
        return [False, False]


def is_valid_date(date_obj, time):
    """ This function check the user selected date and time is valid or not """
    logger.info("Validating the date")
    if (date_obj.date() - datetime.datetime.now().date()).days < 0:
        logger.info(f"date is a past date ")
        logger.info(date_obj.date)
        return False
    elif date_obj.date() == datetime.datetime.now().date():  # checking the date is today or not
        logger.info("the date is today")
        if time == "morning":  # if the date is today morning slot is not available
            logger.info("morning is not possible for today")
            return False
    logger.info("date validation completed successfully")
    return True


def is_out_of_stock(user):
    """ This function checks the stock availability of the product """
    logger.info(f"checking availability of stocks .... for user {user}")
    for item in user.cart.items.all():

        if item.item.type_of_quantity:
            reduction_in_stock = item.weight_variants * item.quantity / 1000
        else:
            reduction_in_stock = item.quantity
        if item.item.stock - reduction_in_stock < 0:
            logger.warning(f"{item.item} is out of stock")
            return item.item
    logger.info(f"checking completed all items are available for user {user} ")
    return False


def use_points(user, amount):
    logger.info(f"{user.username} requested to use points {user.tokens.points} ")
    return amount - user.tokens.points


def reduce_points(user):
    logger.info("user used points to checkout making points zero")
    user.tokens.points = 0
    user.tokens.save()
    print(user.tokens.points)


def add_points(token):
    """ Function to add points to user when first purchase occurs """
    logger.info("performing  adding points")
    invite_token = Tokens.objects.get(private_token=token)
    logger.info(f"user is invited by {invite_token.user.username}, adding 40 points... ")
    invite_token.total_points_yet += 40
    invite_token.points += 40
    logger.info("points adding completed")
    invite_token.save()


def is_valid_coupon(user, coupon_code, amount):
    """
    This function validates the specified coupon applicable or not
    Returns a list with first element will be the status (boolean) second element is the error if not valid
    Returns [True] if the coupon is valid
    """
    logger.info(f"validating coupon {coupon_code} with amount {amount}")
    if not coupon_code:  # checks the coupon is existing one
        return [False, "coupon code does not exist"]
    coupon_obj = Coupon.objects.filter(code__iexact=coupon_code).first()
    if not coupon_obj:
        logger.info("coupon does not exist")
        return [False, "coupon code does not exist"]
    logger.info(f"found coupon object {coupon_obj}")
    order_with_same_cpn = Orders.objects.filter(user__exact=user, coupon=coupon_obj)
    if order_with_same_cpn:
        logger.info(f" already applied {coupon_code} for order {order_with_same_cpn} ")
        return [False, "coupon code does not exist"]
    if coupon_obj.expired:  # check the coupon expired or not
        return [False, "coupon code does not exist"]
    if coupon_obj.user_specific_status:  # checks the coupon is user specific or not
        if coupon_obj.specific_user != user:  # check the specific user is not the requested user
            return [False, "coupon code does not exist"]
    if coupon_obj.minimum_price > amount:  # checks the minimum price condition
        logger.info(f"This coupon is applicable to the amount greater than {coupon_obj.minimum_price}")
        return [False, f"This coupon is applicable to the amount greater than {coupon_obj.minimum_price} "]

    return [True]


def apply_coupon(user, coupon_code, amount):
    """
    This function apply the coupon code and
    """
    logger.info(f"{user} Requested to apply the coupon  {coupon_code}")
    coupon_obj = Coupon.objects.filter(code__iexact=coupon_code).first()

    if coupon_obj:
        logger.info("Found coupon corresponding to requested coupon ")
        if is_valid_coupon(user, coupon_code, amount)[0]:
            logger.info("Requested coupon is a valid coupon ")
            logger.info(f"amount before applying coupon is {amount} ")
            if coupon_obj.discount_type == 0:  # constant type coupon
                amount -= coupon_obj.discount_value
                logger.info(f"amount after applying coupon is {amount} ")
            else:  # percentage type
                amount *= (100 - coupon_obj.discount_value) / 100
                logger.info(f"amount after applying coupon is {amount} ")

    return amount


def total_amount(user, address_obj, coupon_code='', points=False, without_coupon=False):
    """
    This function returns the total amount of the cart items of the user
    Return 0 if the amount is zero
    return amount + delivery charge if amount less than 500
    return amount if amount more than 500
    If any coupon code is present it will apply before adding the delivery charge if any
    """
    logger.info(
        f"calculating total amount for user {user},address-obj ={address_obj}  coupon-{coupon_code} points-{points}")
    cart = user.cart
    amount = 0
    actual_amount = 0
    for item in cart.items.all():
        if item.quantity > 0:
            if item.is_cleaned:
                actual_amount += (item.quantity * item.item.cleaned_price * item.weight_variants / 1000)
                amount = actual_amount * (100 - item.item.discount) / 100
            else:
                if item.item.type_of_quantity:
                    actual_amount += item.quantity * item.item.price * item.weight_variants / 1000
                    amount = actual_amount * (100 - item.item.discount) / 100
                else:
                    actual_amount += item.quantity * item.item.price
                    amount = actual_amount * (100 - item.item.discount) / 100
        elif item.quantity < 0:
            if item.is_cleaned:
                actual_amount += -item.quantity * item.item.cleaned_price * item.weight_variants / 1000
                amount = actual_amount * (100 - item.item.discount) / 100
            else:
                if item.item.type_of_quantity:
                    actual_amount -= item.quantity * item.item.price * item.weight_variants / 1000
                    amount = actual_amount * (100 - item.item.discount) / 100
                else:
                    actual_amount -= item.quantity * item.item.price
                    amount = actual_amount * (100 - item.item.discount) / 100
    logger.info(f"Amount calculated before adding delivery charge is {amount}")
    if amount <= 0:  # if the amount is 0 then it should not add the delivery charge
        return 0, 0

    if not without_coupon:
        if coupon_code:
            amount = apply_coupon(user, coupon_code, amount)

    if amount < 500:  # if amount lee than 500 it will apply the coupon if any and add delivery charge
        logger.info(f"Adding delivery charge .... for amount {amount} ")
        amount += address_obj.delivery_charge
    actual_amount += address_obj.delivery_charge
    if points:
        amount = use_points(user, amount)
        logger.info(f"applied coupon ! Now the amount is {amount} ")
    logger.info(f"total amount adding all charges and offers {amount}  actual amount {actual_amount}")
    return amount, actual_amount


def is_valid_review(user,item):
    exising_review = Reviews.objects.filter(user=user, item=item)
    if exising_review:
        return False, "you cant write more than one review for a product"
    orders = Orders.objects.filter(user=user, status="d")

    for order in orders:
        items = OrderItem.objects.filter(order=order, item=item)
        print(items)
        if items:
            break
    else:
        print("not created")
        return False, "you cant write review for the product that you are not purchase"
    return True, ''


def verify_signature(request):
    logger.info("Signature verification taking place")
    try:
        signature_payload = request.GET['razorpay_payment_link_id'] + '|' + \
                            request.GET['razorpay_payment_link_reference_id'] + '|' + \
                            request.GET['razorpay_payment_link_status'] + '|' + \
                            request.GET['razorpay_payment_id']
        signature_payload = bytes(signature_payload, 'utf-8')
        byte_key = bytes(settings.razorpay_key_secret, 'utf-8')
        generated_signature = hmac.new(byte_key, signature_payload, hashlib.sha256).hexdigest()
        if generated_signature == request.GET["razorpay_signature"]:
            logger.info("Signature verification successfully completed")
            return True
        else:
            logger.warning("signature verification failed")
            return False
    except ValueError:
        logger.warning("signature verification failed value error")
        return False
    except Exception as e:
        logger.warning("signature verification failed")
        logger.warning(e)


def handle_payment(transaction_id, payment_status):
    try:
        transaction_details = TransactionDetails.objects.get(transaction_id=transaction_id)
        transaction_details.payment_status = payment_status
        logger.info(f"payment status {transaction_details.payment_status}")
        #   temp order will have the intermediate  order details between checkout and payment
        #   the items added after checkout will not be in temp order
        logger.info("collecting data  from temporary order ")
        temp_order = TempOrder.objects.get(payment_id=transaction_details.payment_id)
        logger.info(f"temp order = {temp_order.payment_id}")
        temp_items = TempItem.objects.filter(order=temp_order)
        user = transaction_details.user
        logger.info(f"user - {user.username}")
        cart = user.cart
        if temp_order.coupon:
            coupon_obj = Coupon.objects.filter(code=temp_order.coupon)
            print(coupon_obj, temp_order.coupon)
            logger.info(f"Payment done by using coupon {temp_order.coupon.code}")
            order = Orders.objects.create(user=user, date=temp_order.date, time=temp_order.time[0],
                                          address_id=temp_order.address_id,
                                          total=transaction_details.total,
                                          status="p", coupon=temp_order.coupon, used_points=temp_order.used_points)
        else:
            order = Orders.objects.create(user=user, date=temp_order.date, time=temp_order.time[0],
                                          address_id=temp_order.address_id,
                                          total=transaction_details.total, status="p",
                                          used_points=temp_order.used_points)
        logger.info("creating order")
        order.save()
        if order.used_points:
            reduce_points(user)
        transaction_details.order = order
        transaction_details.save()

        token = user.tokens
        token.amount_saved += transaction_details.amount_saved
        if not token.first_purchase_done:
            logger.info("first purchase ")
            if token.invite_token:  # All user may not be invite token that's why this check is here
                logger.info(f"{user.username} is invited by {token.invite_token} token")
                add_points(token.invite_token)  # This function add points if token is valid
            token.first_purchase_done = True  # after first purchase this will executed and make is True
        token.save()
        logger.info(f"first purchase done status = {user.tokens.first_purchase_done}")

        create_order_items(cart, temp_items, order)
        temp_order.delete()
        logger.info("order creation completed")
    except TempOrder.DoesNotExist:
        logger.warning("Temporary order does not exist  already created an order from this")
    except Exception as ex:
        logger.critical(f"order not created exception {ex} ")


def create_order_items(cart, temp_items, order):
    logger.info("creating order items")
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
    return distance * 1.45


def get_delivery_charge(location):
    distance = distance_between(settings.location, [location[0], location[1]])
    if distance <= 10:
        return 30
    else:
        return 60
