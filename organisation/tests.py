# Create your tests here.
import pandas

from billing.models import HsnCode

loc = ("HSN_SAC.xlsx")
data = pandas.read_excel(loc)
for i in data.values:
    HsnCode.objects.get_or_create(code=str(i[0]), description=i[1])
