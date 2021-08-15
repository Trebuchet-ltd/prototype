"""
This file contains all the supporting functions needed for api view sets

"""
import requests
from .models import *
from django.contrib.gis.geos import GEOSGeometry
from requests.auth import HTTPBasicAuth
import datetime
import prototype.settings as settings


def is_available_district(pincode):
    """
    This function find the district of corresponding pincode and check the  district is available for delivery
    returns true if available else false

    """
    try:
        district = requests.get(f'https://api.postalpincode.in/pincode/{pincode}').json()[0].get("PostOffice")[
            0].get("District")
        print(district)
        # district obj contains the district if it is added to database else return null queryset
        district_obj = District.objects.filter(district_name=district)

        # this check whether the the district added to the database and it is available for delivery
        if not (district_obj and district_obj[0].Available_status):
            return False
    except TypeError:
        pass
    else:
        return True


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


def create_temp_order(cart, payment_id, date, time, address_obj, coupon_code=''):
    """
    This will create an intermediate object of order and order items for storing the current cart items ans details

    """
    coupon_obj = Coupon.objects.filter(code=coupon_code).first()
    if coupon_obj:
        order = TempOrder.objects.create(payment_id=payment_id, date=date, time=time,
                                         address_id=address_obj.id, coupon=coupon_obj)
        order.save()
    else:
        order = TempOrder.objects.create(payment_id=payment_id, date=date, time=time,
                                         address_id=address_obj.id)
        order.save()
    for item in cart.items.all():
        temp_item = TempItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                            weight_variants=item.weight_variants,
                                            is_cleaned=item.is_cleaned)
        temp_item.save()


def cancel_last_payment_links(user):
    print("This is called")
    transaction_details = TransactionDetails.objects.filter(user=user, payment_status="created")
    key_secret = settings.razorpay_key_secret
    key_id = settings.razorpay_key_id
    for transaction in transaction_details:
        url = f'https://api.razorpay.com/v1/payment_links/{transaction.payment_id}/cancel'
        print(f"canceling  {transaction.payment_id}")
        requests.post(url,
                      headers={'Content-type': 'application/json'},
                      auth=HTTPBasicAuth(key_id, key_secret))
        transaction.delete()


def get_payment_link(user, amount, address_obj):
    """
    This Function returns thr payment url for that particular checkout
    Returns a list with payment link and payment id created by razorpay
    """

    key_secret = settings.razorpay_key_secret
    call_back_url = settings.webhook_call_back_url
    key_id = settings.razorpay_key_id
    cancel_last_payment_links(user)
    transaction_id = create_new_unique_id()
    transaction_details = TransactionDetails(transaction_id=transaction_id, user=user, total=amount)
    transaction_details.save()

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
        data = x.json()
        transaction_details.payment_id = data.get("id")
        transaction_details.payment_status = data.get("status")
        transaction_details.save()
        payment_url = data.get('short_url')
        return [payment_url, transaction_details.payment_id]
    except Exception as e:
        print(e)
        return False


def is_valid_date(date_obj, time):
    """ This function check the user selected date and time is valid or not """

    if (date_obj.date() - datetime.datetime.now().date()).days < 0:
        return False
    elif date_obj.date() == datetime.datetime.now().date():  # checking the date is today or not
        if time == "morning":  # if the date is today morning slot is not available
            return False
    return True


def is_out_of_stock(user):
    """ This function checks the stock availability of the product """
    for item in user.cart.items.all():
        reduction_in_stock = item.weight_variants * item.quantity / 1000
        if item.item.stock - reduction_in_stock <= 0:
            return item.item
    return False


def is_valid_coupon(user, coupon_code, amount):
    """
    This function validates the specified coupon applicable or not
    Returns a list with first element will be the status (boolean) second element is the error if not valid
    Returns [True] if the coupon is valid
    """
    coupon_obj = Coupon.objects.filter(code=coupon_code).first()

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

    coupon_obj = Coupon.objects.filter(code=coupon_code).first()

    if coupon_obj:
        if is_valid_coupon(user, coupon_code, amount)[0]:
            print("valid")
            if coupon_obj.discount_type == 0:  # constant type coupon
                amount -= coupon_obj.discount_value
            else:  # percentage type
                amount *= (100 - coupon_obj.discount_value) / 100
    return amount


def total_amount(user, address_obj, coupon_code='', without_coupon=False):
    """
    This function returns the total amount of the cart items of the user
    Return 0 if the amount is zero
    return amount + delivery charge if amount less than 500
    return amount if amount more than 500
    If any coupon code is present it will apply before adding the delivery charge if any

    """
    cart = user.cart
    amount = 0

    for item in cart.items.all():
        if item.quantity > 0:
            if item.is_cleaned:
                amount += item.quantity * item.item.cleaned_price * item.weight_variants / 1000
            else:
                amount += item.quantity * item.item.price * item.weight_variants / 1000

        elif item.quantity < 0:
            if item.is_cleaned:
                amount += -item.quantity * item.item.cleaned_price * item.weight_variants / 1000
            else:
                amount += -item.quantity * item.item.price * item.weight_variants / 1000

    if amount <= 0:  # if the amount is 0 then it should not add the delivery charge
        return 0

    if not without_coupon:
        if coupon_code:
            print(amount)
            amount = apply_coupon(user, coupon_code, amount)

    if amount < 500:  # if amount lee than 500 it will apply the coupon if any and add delivery charge
        amount += address_obj.delivery_charge
    return amount


def is_valid_point(user, points):
    token = user.tokens
    if token.points - points < 0:
        return [False, "not enough points "]
    return [True]


def use_points(user,amount,points):
    if is_valid_point(user, points)[0]:
        amount = amount - points
    return amount


def reduce_points(user, points):
    user.tokens.points -= points
    user.tokens.points.save()


def add_points(token):
    """ Function to add points to user when first purchase occurs """
    purchase_done = Tokens.objects.get(invite_token=token).first_purchase_done
    if not purchase_done:
        invite_token = Tokens.objects.get(private_token=token)
        invite_token.total_points_yet += 40
        invite_token.points += 40
        invite_token.save()
        return True

    return False


def create_order_items(cart, temp_items, order):
    for item in temp_items.all():
        order_item = OrderItem.objects.create(item=item.item, quantity=item.quantity, order=order,
                                              weight_variants=item.weight_variants,
                                              is_cleaned=item.is_cleaned)
        order_item.save()
        reduction_in_stock = item.weight_variants * item.quantity / 1000
        item.item.stock -= reduction_in_stock
        item.item.save()
        CartItem.objects.filter(item=item.item, weight_variants=item.weight_variants,
                                is_cleaned=item.is_cleaned).delete()

    cart.total = 0
    cart.save()


def distance_between(loc1, loc2):
    pnt1 = GEOSGeometry(f"POINT ({loc1[0]} {loc1[1]})")
    pnt2 = GEOSGeometry(f"POINT ({loc2[0]} {loc2[1]})")
    distance = pnt1.distance(pnt2) * 100
    return distance


def get_delivery_charge(location):
    distance = distance_between(settings.location, [location[0], location[1]])
    if distance <= 10:
        return 30
    else:
        return 60
