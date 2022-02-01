from django.db import models


# Create your models here.

class Organisation(models.Model):
    name = models.CharField(max_length=30)
    address = models.ForeignKey("home.Addresses", related_name='organisation', on_delete=models.PROTECT)
    gst_no = models.CharField(max_length=16)
    show_own_website = models.BooleanField()
    mobile_number = models.CharField(max_length=13)
    c_invoice_count = models.PositiveIntegerField(default=0)
    b_invoice_count = models.PositiveIntegerField(default=0)
    c_invoice_prefix = models.CharField(max_length=5)
    b_invoice_prefix = models.CharField(max_length=5)

    def __str__(self):
        return self.name
