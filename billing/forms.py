from django.forms import ModelForm

from billing.models import BillingProduct


class ProductForm(ModelForm):
    class Meta:
        model = BillingProduct
        fields = ['title', 'code', 'price', 'price2', 'price3', 'stock', 'discount', 'gst_percent', 'product_hsn']

    def get_hsn(self):
        return self.instance.product_hsn
