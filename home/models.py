from django.db import models
from django.conf import settings

# Create your models here.
class product(models.Model):
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
    meat  = models.CharField(max_length=1, choices=meat_type)

    def __str__(self):
        return self.title

        
class imageModel(models.Model):
    title     = models.TextField(max_length=10)
    mainimage = models.ImageField(upload_to="static/images/",null = True)
    image     = models.ForeignKey(product,related_name = 'images' , on_delete=models.CASCADE)

    def __str__(self):
        return self.title
       
class cartModel(models.Model):
    user         = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="cart", on_delete=models.CASCADE)
    total        = models.FloatField()
    address      = models.TextField(max_length=255)
    pincode      = models.IntegerField()
    state        = models.TextField(max_length= 20)

class cart_item(models.Model):
    item   = models.ForeignKey(product,related_name="cart_item", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    cart     = models.ForeignKey(cartModel, related_name= "items", on_delete=models.CASCADE)
    

        