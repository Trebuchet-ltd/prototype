from django.forms import ModelForm

from home.models import Product


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'code', 'description', 'short_description', 'price', 'stock',
                  'meat', 'bestSeller', "weight", 'rating', 'product_hsn',
                  'weight_variants', 'pieces', 'serves', 'can_be_cleaned', 'cleaned_price', "discount",
                  'nutrition', 'product_gst_percentage', 'product_rate_with_gst']
