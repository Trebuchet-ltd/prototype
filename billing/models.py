from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from organisation.models import Organisation


class HsnCode(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    description = models.TextField(max_length=1500, blank=True, null=True)
    gst_percent = models.FloatField(validators=[MaxValueValidator(100), MinValueValidator(0)], blank=True, null=True)

    def __str__(self):
        return self.code


class BillingProduct(models.Model):
    title = models.CharField(max_length=255)
    product_hsn = models.ForeignKey(HsnCode, on_delete=models.SET_NULL, blank=True, null=True)
    product = models.ForeignKey("home.Product", on_delete=models.PROTECT, blank=True, null=True, related_name='sellers')
    code = models.CharField(max_length=8)
    price = models.FloatField()
    stock = models.IntegerField(default=0)
    discount = models.PositiveIntegerField(validators=[MaxValueValidator(100)], default=0)
    price2 = models.FloatField(default=0)
    price3 = models.FloatField(default=0)
    gst_percent = models.PositiveIntegerField(validators=[MaxValueValidator(100)], default=0)
    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT, blank=True, null=True)
    can_be_cleaned = models.BooleanField(default=False)
    cleaned_price = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.title
