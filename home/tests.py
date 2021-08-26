from django.test import TestCase
from .functions import *
from .models import *
from django.contrib.auth.models import User
import datetime
import copy


class CheckoutTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@gmail.com', password='password', username='test',
                                             first_name='test')
        Tokens.objects.get_or_create(user=self.user, points=40)
        cart, _ = CartModel.objects.get_or_create(user=self.user)
        self.coupon = Coupon.objects.create(minimum_price=100, discount_type=0, discount_value=50)
        self.address_obj = Addresses.objects.create(name="test1", address='test', pincode=679357,
                                                    user=self.user, phone='9072124291', state='kerala',
                                                    delivery_charge=60)
        product1 = Product.objects.create(title='test_product1', type_of_quantity=0,
                                          short_description='test_description', description='test_description',
                                          price=100, stock=10, )
        # product2 = Product.objects.create(title='test_product2', type_of_quantity=0,
        #                                   short_description='test_description', description='test_description',
        #                                   price=200, stock=10, )
        CartItem.objects.create(cart=cart, item=product1, quantity=2)
        # CartItem.objects.create(cart=cart, item=product2, quantity=2)

    def test_amount_without_coupon_point(self):
        total, actual = total_amount(self.user, self.address_obj)
        self.assertEqual(int(total), 260)
        self.assertEqual(int(actual), 260)

    def test_amount_with_coupon(self):
        total, actual = total_amount(self.user, self.address_obj, self.coupon.code)
        self.assertEqual(int(total), 210)
        self.assertEqual(int(actual), 260)

    def test_amount_with_point(self):
        total, actual = total_amount(self.user, self.address_obj, points=True)
        self.assertEqual(int(total), 220)
        self.assertEqual(int(actual), 260)

    def test_amount_with_coupon_point(self):
        total, actual = total_amount(self.user, self.address_obj, self.coupon.code, True)
        self.assertEqual(int(total), 170)
        self.assertEqual(int(actual), 260)

    def test_payment_link(self):
        total, actual = total_amount(self.user, self.address_obj)
        payment_url, payment_id = get_payment_link(self.user, total, actual - total, self.address_obj)
        self.assertTrue(payment_id, msg="Payment id is null")
        self.assertTrue(payment_url, msg="Payment url is null")

    def test_temp_order(self):
        create_temp_order(self.user, "payment", str(datetime.date.today()), 'morning', self.address_obj)
        temp = TempOrder.objects.get(payment_id='payment')
        self.assertIsNotNone(temp, msg="temp order is null")
        temp_items = TempItem.objects.filter(order=temp)
        self.assertIsNotNone(temp_items, msg="temp item  is null")


class HandlePaymentTestCase(TestCase):

    def setUp(self) -> None:
        self.old_user = User.objects.create_user(email='old@gmail.com', password='password', username='old',
                                                 first_name='old')
        token,_ = Tokens.objects.get_or_create(user=self.old_user)

        self.user = User.objects.create_user(email='test@gmail.com', password='password', username='test',
                                             first_name='test')
        Tokens.objects.get_or_create(user=self.user, points=40,invite_token=token.private_token)
        self.cart, _ = CartModel.objects.get_or_create(user=self.user)
        self.product1 = Product.objects.create(title='test_product1', type_of_quantity=0,
                                               short_description='test_description', description='test_description',
                                               price=100, stock=10, )
        self.product2 = Product.objects.create(title='test_product2', type_of_quantity=0,
                                               short_description='test_description', description='test_description',
                                               price=200, stock=10, )
        self.address_obj = Addresses.objects.create(name="test1", address='test', pincode=679357,
                                                    user=self.user, phone='9072124291', state='kerala',
                                                    delivery_charge=60)
        self.coupon_constant = Coupon.objects.create(minimum_price=100, discount_type=0, discount_value=50)
        self.coupon_percentage = Coupon.objects.create(minimum_price=100, discount_type=1, discount_value=20)

    def create_requirements(self, coupon=False, point=False):
        CartItem.objects.create(cart=self.cart, item=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, item=self.product2, quantity=3)
        if not coupon and not point:

            self.total, self.actual = total_amount(self.user, self.address_obj)
            self.payment_url, self.payment_id = get_payment_link(self.user, self.total, self.actual - self.total,
                                                                 self.address_obj)

            self.temp_order = create_temp_order(self.user, self.payment_id, str(datetime.date.today()), 'morning',
                                                self.address_obj)
        elif coupon and not point:
            self.total, self.actual = total_amount(self.user, self.address_obj,coupon_code=self.coupon_constant.code)
            self.payment_url, self.payment_id = get_payment_link(self.user, self.total, self.actual - self.total,
                                                                 self.address_obj)

            self.temp_order = create_temp_order(self.user, self.payment_id, str(datetime.date.today()), 'morning',
                                                self.address_obj,self.coupon_constant.code)
        elif point and not coupon:

            self.total, self.actual = total_amount(self.user, self.address_obj, points=True)
            self.payment_url, self.payment_id = get_payment_link(self.user, self.total, self.actual - self.total,
                                                                 self.address_obj)

            self.temp_order = create_temp_order(self.user, self.payment_id, str(datetime.date.today()), 'morning',
                                                self.address_obj, points=True)
        else:

            self.total, self.actual = total_amount(self.user, self.address_obj, self.coupon_constant.code,True)
            self.payment_url, self.payment_id = get_payment_link(self.user, self.total, self.actual - self.total,
                                                                 self.address_obj)

            self.temp_order = create_temp_order(self.user, self.payment_id, str(datetime.date.today()), 'morning',
                                                self.address_obj, self.coupon_constant.code, True)

    def test_first_payment(self):
        self.create_requirements()
        tran = TransactionDetails.objects.get(payment_id=self.payment_id)
        handle_payment(tran.transaction_id, 'paid')
        token = Tokens.objects.get(user=self.user)
        self.assertEqual(token.first_purchase_done, True, 'first purchase status not changed')
        invited_token = Tokens.objects.get(private_token=token.invite_token)
        self.assertEqual(invited_token.points,40, "point is not adding to invited user")

    def test_order_creation(self):
        self.create_requirements()
        tran = TransactionDetails.objects.get(payment_id=self.payment_id)
        temp_items = copy.copy(TempItem.objects.all())
        handle_payment(tran.transaction_id, 'paid')
        order = Orders.objects.get(user=self.user)
        self.assertIsNotNone(order, msg="order is null")
        order_items = OrderItem.objects.filter(order=order)
        self.assertIsNotNone(order_items, "order item is null")
        self.assertEqual(len(temp_items), len(order_items), msg='full temp order items not used to create ')
        for item, temp in zip(order_items, temp_items):
            self.assertEqual(item.item, temp.item, msg='items not match')

    def test_point_reduction(self):
        self.create_requirements(point=True)
        tran = TransactionDetails.objects.get(payment_id=self.payment_id)
        handle_payment(tran.transaction_id, 'paid')
        points = Tokens.objects.get(user=self.user).points
        self.assertEqual(points, 0, msg="Points not reduced ")




