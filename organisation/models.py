from django.db import models


# Create your models here.

class Organisation(models.Model):
    name = models.CharField(max_length=30)
    address = models.ForeignKey("home.Addresses", related_name='organisation', on_delete=models.PROTECT)
    gst_no = models.CharField(max_length=16)
    show_own_website = models.BooleanField()
    mobile_number = models.CharField(max_length=13)

# class Products(models.Model):
#     title = models.CharField(max_length=255)
#     product_hsn = models.CharField(max_length=8)
#     price = models.FloatField()
#     stock = models.IntegerField()
#     type_of_quantity = models.IntegerField(default=1, choices=[(1, "weight"), (0, "piece")])
#     product_gst_percentage = models.FloatField(default=0)
#     product_rate_with_gst = models.FloatField(default=0)
