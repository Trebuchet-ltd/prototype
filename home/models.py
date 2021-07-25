from django.db import models
from django.conf import settings
import string
import random


# Create your models here.
class Product(models.Model):
    meat_type = (
        ('c', 'chicken'),
        ('b', 'beef'),
        ('m', 'mutton'),
        ('p', 'pork'),
        ('f', 'fish'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(max_length=2048)
    price = models.FloatField()
    stock = models.IntegerField()
    meat = models.CharField(max_length=1, choices=meat_type)
    bestSeller = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ImageModel(models.Model):
    title = models.TextField(max_length=10)
    mainimage = models.ImageField(upload_to="images/", null=True)
    image = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class CartModel(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="cart", on_delete=models.CASCADE)
    total = models.FloatField(default=0)
    pincode = models.IntegerField(default=0)
    state = models.TextField(max_length=20,default='')


class CartItem(models.Model):
    item = models.ForeignKey(Product, related_name="cart_item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    cart = models.ForeignKey(CartModel, related_name="items", on_delete=models.CASCADE)


class MainPage(models.Model):
    product = models.ForeignKey(Product, related_name="Product", on_delete=models.CASCADE)
    heading = models.TextField(max_length=20)
    description = models.TextField(max_length=255)


class Addresses(models.Model):
    name = models.TextField(max_length=100)
    address = models.TextField(max_length=3000)
    pincode = models.CharField(max_length=6)
    state = models.TextField(max_length=100)
    phone = models.CharField(max_length=12)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="Addresses", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.address}, {self.state}, {self.pincode} (PIN) "

class Orders(models.Model):
    order_status = (
        ('r', 'received'),
        ('p', 'preparing'),
        ('o', 'on route'),
        ('d', 'delivered'),

    )
    order_time =(
        ('m', 'morning'),
        ('e', 'evening')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    total = models.FloatField()
    address = models.ForeignKey(Addresses, related_name="orders", on_delete=models.CASCADE)

    date = models.DateField()
    time = models.CharField(max_length=10,choices=order_time)
    status = models.CharField(max_length=10, choices=order_status, default='preparing')

    def __str__(self):
        return f"{self.user} , date-{self.date} , status -{self.status} "

class OrderItem(models.Model):
    item = models.ForeignKey(Product, related_name="order_item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey(Orders, related_name="order_item", on_delete=models.CASCADE)


class TransactionDetails(models.Model):

    order = models.ForeignKey(Orders, related_name="transaction", on_delete=models.CASCADE,null=True,blank=True)
    # to store the random generated unique id
    transaction_id = models.CharField(max_length=10)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="transaction", on_delete=models.CASCADE)
    # to store the id returned when creating a payment link
    payment_id = models.CharField(max_length=20, default="")
    payment_status = models.CharField(max_length=20, default="")

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def create_new_id():
    not_unique = True
    unique_id = id_generator()
    while not_unique:
        unique_id = id_generator()
        if not Tokens.objects.filter(private_token=unique_id):
            not_unique = False
    return str(unique_id)


class Tokens(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='tokens', on_delete=models.CASCADE)
    private_token = models.CharField(max_length=10, unique=True, default=create_new_id)
    invited = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    reviews = models.IntegerField(default=0)
    invite_token = models.CharField(max_length=10, blank=True, null=True)
