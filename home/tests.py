from django.test import TestCase
from .functions import *
from .models import *
# Create your tests here.
from django.contrib.auth.models import User


class TotalAmountTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@gmail.com', password='password', username='test',
                                        first_name='test')
        Tokens.objects.get_or_create(user=self.user, points=40)
        cart, _ = CartModel.objects.get_or_create(user=self.user)
        self.coupon = Coupon.objects.create(minimum_price=100, discount_type=0, discount_value=50)
        self.address_obj=Addresses.objects.create(name="test1", address='test', pincode=679357,
                                 user=self.user, phone=9072124291,state='kerala', delivery_charge=60)
        product1 = Product.objects.create(title='test_product1', type_of_quantity=0, short_description='test_description',description='test_description',
                                          price=100, stock=10,)
        CartItem.objects.create(cart=cart, item=product1, quantity=2)

    def test_amount_without_coupon_point(self):

        total,actual= total_amount(self.user, self.address_obj)
        self.assertEqual(int(total), 260)
        self.assertEqual(int(actual), 260)

    def test_amount_with_coupon(self):
        total, actual = total_amount(self.user, self.address_obj,self.coupon.code)
        print(total, actual)
        self.assertEqual(int(total), 210)
        self.assertEqual(int(actual), 260)

    def test_amount_with_point(self):
        total, actual = total_amount(self.user, self.address_obj,points=True)
        print(total, actual)
        self.assertEqual(int(total), 220)
        self.assertEqual(int(actual), 260)

    def test_amount_with_coupon_point(self):
        total, actual = total_amount(self.user, self.address_obj,self.coupon.code, True)
        print(total, actual)
        self.assertEqual(int(total), 170)
        self.assertEqual(int(actual), 260)
