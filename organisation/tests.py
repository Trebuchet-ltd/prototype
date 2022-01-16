# Create your tests here.
import pandas

from billing.models import HsnCode

loc = ("HSN_SAC.xlsx")
data = pandas.read_excel(loc)
for i in data.values:
    HsnCode.objects.get_or_create(code=str(i[0]), description=i[1])


from billing.models import HsnCode, BillingProduct
import pandas
from organisation.models import Organisation
org = Organisation.objects.get(id=2)
loc = ("PRODUCTS.xlsx")
data = pandas.read_excel(loc)
for i in data.values:
    try:
        print(i[0])
        hsn = HsnCode.objects.get(code=i[4])
        BillingProduct.objects.get_or_create(title=i[1], code=i[0], product_hsn=hsn, gst_percent=i[5], price=i[2],
                                             price2=i[3], price3=i[3], organisation__id=2)
    except HsnCode.DoesNotExist:
        pass
