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
    rating = models.IntegerField(default=0)
    weight = models.FloatField(default=1)

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

    def __str__(self):
        return f"{self.user}'s cart"

class CartItem(models.Model):
    item = models.ForeignKey(Product, related_name="cart_item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    cart = models.ForeignKey(CartModel, related_name="items", on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.item} - {self.quantity} "


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
    latitude = models.FloatField(null=True,blank=True)
    longitude = models.FloatField(null=True,blank=True)
    delivery_charge = models.IntegerField(null=True,blank=True,choices=((1,30),(2,60)))
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
    is_seen = models.IntegerField(default=0,blank=True, null=True, help_text='1->Seen, 0->Not seen',
                                    choices=(
                                        (1, 'Seen'), (0, 'Not seen')
                                    ))
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
    # The order date ,time ,and adress id
    date = models.DateField(blank=True,null=True)
    time = models.CharField(max_length=20, default='')
    adress_id = models.CharField(max_length=10, default='')

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


class AvailableState(models.Model):
    states = (('1', 'Andaman and Nicobar Islands'), ('2', 'Andhra Pradesh'), ('3', 'Arunachal Pradesh'), ('4', 'Assam'), ('5', 'Bihar'),
              ('6', 'Chandigarh'), ('7', 'Chhattisgarh'), ('8', 'Dadra and Nagar Haveli'), ('9', 'Delhi'), ('10', 'Goa'),
              ('11', 'Gujarat'), ('12', 'Haryana'), ('13', 'Himachal Pradesh'), ('14', 'Jammu and Kashmir'), ('15', 'Jharkhand'), ('16', 'Karnataka'),
              ('17', 'Kerala'), ('18', 'Ladakh'), ('19', 'Lakshadweep'), ('20', 'Madhya Pradesh'), ('21', 'Maharashtra'), ('22', 'Manipur'),
              ('23', 'Meghalaya'), ('24', 'Mizoram'), ('25', 'Nagaland'), ('26', 'Odisha'), ('27', 'Puducherry'), ('28', 'Punjab'), ('29', 'Rajasthan'),
              ('30', 'Sikkim'), ('31', 'Tamil Nadu'), ('32', 'Telangana'), ('33', 'Tripura'), ('34', 'Uttar Pradesh'), ('35', 'Uttarakhand'),
              ('36', 'West Bengal'),('37', 'Daman and Diu'))

    state_name = models.CharField(max_length=30 , unique=True, choices=states)

    def __str__(self):

        return self.states[int(self.state_name)-1][1]


class District(models.Model):
    district_choices = [(None, 'District'), ('Anantapur', 'Anantapur'), ('Chittoor', 'Chittoor'),
                    ('East Godavari', 'East Godavari'),
                    ('Guntur', 'Guntur'),
                    ('Krishna', 'Krishna'), ('Kurnool', 'Kurnool'), ('Nellore', 'Nellore'), ('Prakasam', 'Prakasam'),
                    ('Srikakulam', 'Srikakulam'), ('Visakhapatnam', 'Visakhapatnam'), ('Vizianagaram', 'Vizianagaram'),
                    ('West Godavari', 'West Godavari'), ('YSR Kadapa', 'YSR Kadapa'), ('Tawang', 'Tawang'),
                    ('West Kameng', 'West Kameng'), ('East Kameng', 'East Kameng'), ('Papum Pare', 'Papum Pare'),
                    ('Kurung Kumey', 'Kurung Kumey'), ('Kra Daadi', 'Kra Daadi'),
                    ('Lower Subansiri', 'Lower Subansiri'),
                    ('Upper Subansiri', 'Upper Subansiri'), ('West Siang', 'West Siang'), ('East Siang', 'East Siang'),
                    ('Siang', 'Siang'), ('Upper Siang', 'Upper Siang'), ('Lower Siang', 'Lower Siang'),
                    ('Lower Dibang Valley', 'Lower Dibang Valley'), ('Dibang Valley', 'Dibang Valley'),
                    ('Anjaw', 'Anjaw'),
                    ('Lohit', 'Lohit'), ('Namsai', 'Namsai'), ('Changlang', 'Changlang'), ('Tirap', 'Tirap'),
                    ('Longding', 'Longding'),
                    ('Baksa', 'Baksa'), ('Barpeta', 'Barpeta'), ('Biswanath', 'Biswanath'),
                    ('Bongaigaon', 'Bongaigaon'),
                    ('Cachar', 'Cachar'), ('Charaideo', 'Charaideo'), ('Chirang', 'Chirang'), ('Darrang', 'Darrang'),
                    ('Dhemaji', 'Dhemaji'), ('Dhubri', 'Dhubri'), ('Dibrugarh', 'Dibrugarh'), ('Goalpara', 'Goalpara'),
                    ('Golaghat', 'Golaghat'), ('Hailakandi', 'Hailakandi'), ('Hojai', 'Hojai'), ('Jorhat', 'Jorhat'),
                    ('Kamrup Metropolitan', 'Kamrup Metropolitan'), ('Kamrup', 'Kamrup'),
                    ('Karbi Anglong', 'Karbi Anglong'),
                    ('Karimganj', 'Karimganj'), ('Kokrajhar', 'Kokrajhar'), ('Lakhimpur', 'Lakhimpur'),
                    ('Majuli', 'Majuli'),
                    ('Morigaon', 'Morigaon'), ('Nagaon', 'Nagaon'), ('Nalbari', 'Nalbari'),
                    ('Dima Hasao', 'Dima Hasao'),
                    ('Sivasagar', 'Sivasagar'), ('Sonitpur', 'Sonitpur'),
                    ('South Salmara-Mankachar', 'South Salmara-Mankachar'),
                    ('Tinsukia', 'Tinsukia'), ('Udalguri', 'Udalguri'), ('West Karbi Anglong', 'West Karbi Anglong'),
                    ('Araria', 'Araria'), ('Arwal', 'Arwal'), ('Aurangabad', 'Aurangabad'), ('Banka', 'Banka'),
                    ('Begusarai', 'Begusarai'), ('Bhagalpur', 'Bhagalpur'), ('Bhojpur', 'Bhojpur'), ('Buxar', 'Buxar'),
                    ('Darbhanga', 'Darbhanga'), ('East Champaran (Motihari)', 'East Champaran (Motihari)'),
                    ('Gaya', 'Gaya'),
                    ('Gopalganj', 'Gopalganj'), ('Jamui', 'Jamui'), ('Jehanabad', 'Jehanabad'),
                    ('Kaimur (Bhabua)', 'Kaimur (Bhabua)'),
                    ('Katihar', 'Katihar'), ('Khagaria', 'Khagaria'), ('Kishanganj', 'Kishanganj'),
                    ('Lakhisarai', 'Lakhisarai'),
                    ('Madhepura', 'Madhepura'), ('Madhubani', 'Madhubani'), ('Munger (Monghyr)', 'Munger (Monghyr)'),
                    ('Muzaffarpur', 'Muzaffarpur'), ('Nalanda', 'Nalanda'), ('Nawada', 'Nawada'), ('Patna', 'Patna'),
                    ('Purnia (Purnea)', 'Purnia (Purnea)'), ('Rohtas', 'Rohtas'), ('Saharsa', 'Saharsa'),
                    ('Samastipur', 'Samastipur'),
                    ('Saran', 'Saran'), ('Sheikhpura', 'Sheikhpura'), ('Sheohar', 'Sheohar'),
                    ('Sitamarhi', 'Sitamarhi'),
                    ('Siwan', 'Siwan'), ('Supaul', 'Supaul'), ('Vaishali', 'Vaishali'),
                    ('West Champaran', 'West Champaran'),
                    ('Chandigarh', 'Chandigarh'), ('Balod', 'Balod'), ('Baloda Bazar', 'Baloda Bazar'),
                    ('Balrampur', 'Balrampur'),
                    ('Bastar', 'Bastar'), ('Bemetara', 'Bemetara'), ('Bijapur', 'Bijapur'), ('Bilaspur', 'Bilaspur'),
                    ('Dantewada (South Bastar)', 'Dantewada (South Bastar)'), ('Dhamtari', 'Dhamtari'),
                    ('Durg', 'Durg'),
                    ('Gariyaband', 'Gariyaband'), ('Janjgir-Champa', 'Janjgir-Champa'), ('Jashpur', 'Jashpur'),
                    ('Kabirdham (Kawardha)', 'Kabirdham (Kawardha)'),
                    ('Kanker (North Bastar)', 'Kanker (North Bastar)'),
                    ('Kondagaon', 'Kondagaon'), ('Korba', 'Korba'), ('Korea (Koriya)', 'Korea (Koriya)'),
                    ('Mahasamund', 'Mahasamund'),
                    ('Mungeli', 'Mungeli'), ('Narayanpur', 'Narayanpur'), ('Raigarh', 'Raigarh'), ('Raipur', 'Raipur'),
                    ('Rajnandgaon', 'Rajnandgaon'), ('Sukma', 'Sukma'), ('Surajpur  ', 'Surajpur  '),
                    ('Surguja', 'Surguja'),
                    ('Dadra & Nagar Haveli', 'Dadra & Nagar Haveli'), ('Daman', 'Daman'), ('Diu', 'Diu'),
                    ('Central Delhi', 'Central Delhi'), ('East Delhi', 'East Delhi'), ('New Delhi', 'New Delhi'),
                    ('North Delhi', 'North Delhi'), ('North East  Delhi', 'North East  Delhi'),
                    ('North West  Delhi', 'North West  Delhi'), ('Shahdara', 'Shahdara'),
                    ('South Delhi', 'South Delhi'),
                    ('South East Delhi', 'South East Delhi'), ('South West  Delhi', 'South West  Delhi'),
                    ('West Delhi', 'West Delhi'),
                    ('North Goa', 'North Goa'), ('South Goa', 'South Goa'), ('Ahmedabad', 'Ahmedabad'),
                    ('Amreli', 'Amreli'),
                    ('Anand', 'Anand'), ('Aravalli', 'Aravalli'), ('Banaskantha (Palanpur)', 'Banaskantha (Palanpur)'),
                    ('Bharuch', 'Bharuch'), ('Bhavnagar', 'Bhavnagar'), ('Botad', 'Botad'),
                    ('Chhota Udepur', 'Chhota Udepur'),
                    ('Dahod', 'Dahod'), ('Dangs (Ahwa)', 'Dangs (Ahwa)'), ('Devbhoomi Dwarka', 'Devbhoomi Dwarka'),
                    ('Gandhinagar', 'Gandhinagar'), ('Gir Somnath', 'Gir Somnath'), ('Jamnagar', 'Jamnagar'),
                    ('Junagadh', 'Junagadh'),
                    ('Kachchh', 'Kachchh'), ('Kheda (Nadiad)', 'Kheda (Nadiad)'), ('Mahisagar', 'Mahisagar'),
                    ('Mehsana', 'Mehsana'),
                    ('Morbi', 'Morbi'), ('Narmada (Rajpipla)', 'Narmada (Rajpipla)'), ('Navsari', 'Navsari'),
                    ('Panchmahal (Godhra)', 'Panchmahal (Godhra)'), ('Patan', 'Patan'), ('Porbandar', 'Porbandar'),
                    ('Rajkot', 'Rajkot'), ('Sabarkantha (Himmatnagar)', 'Sabarkantha (Himmatnagar)'),
                    ('Surat', 'Surat'),
                    ('Surendranagar', 'Surendranagar'), ('Tapi (Vyara)', 'Tapi (Vyara)'), ('Vadodara', 'Vadodara'),
                    ('Valsad', 'Valsad'), ('Ambala', 'Ambala'), ('Bhiwani', 'Bhiwani'),
                    ('Charkhi Dadri', 'Charkhi Dadri'),
                    ('Faridabad', 'Faridabad'), ('Fatehabad', 'Fatehabad'), ('Gurgaon', 'Gurgaon'), ('Hisar', 'Hisar'),
                    ('Jhajjar', 'Jhajjar'), ('Jind', 'Jind'), ('Kaithal', 'Kaithal'), ('Karnal', 'Karnal'),
                    ('Kurukshetra', 'Kurukshetra'), ('Mahendragarh', 'Mahendragarh'), ('Mewat', 'Mewat'),
                    ('Palwal', 'Palwal'),
                    ('Panchkula', 'Panchkula'), ('Panipat', 'Panipat'), ('Rewari', 'Rewari'), ('Rohtak', 'Rohtak'),
                    ('Sirsa', 'Sirsa'),
                    ('Sonipat', 'Sonipat'), ('Yamunanagar', 'Yamunanagar'), ('Bilaspur', 'Bilaspur'),
                    ('Chamba', 'Chamba'),
                    ('Hamirpur', 'Hamirpur'), ('Kangra', 'Kangra'), ('Kinnaur', 'Kinnaur'), ('Kullu', 'Kullu'),
                    ('Lahaul &amp; Spiti', 'Lahaul &amp; Spiti'), ('Mandi', 'Mandi'), ('Shimla', 'Shimla'),
                    ('Sirmaur (Sirmour)', 'Sirmaur (Sirmour)'), ('Solan', 'Solan'), ('Una', 'Una'),
                    ('Anantnag', 'Anantnag'),
                    ('Bandipore', 'Bandipore'), ('Baramulla', 'Baramulla'), ('Budgam', 'Budgam'), ('Doda', 'Doda'),
                    ('Ganderbal', 'Ganderbal'), ('Jammu', 'Jammu'), ('Kargil', 'Kargil'), ('Kathua', 'Kathua'),
                    ('Kishtwar', 'Kishtwar'), ('Kulgam', 'Kulgam'), ('Kupwara', 'Kupwara'), ('Leh', 'Leh'),
                    ('Poonch', 'Poonch'),
                    ('Pulwama', 'Pulwama'), ('Rajouri', 'Rajouri'), ('Ramban', 'Ramban'), ('Reasi', 'Reasi'),
                    ('Samba', 'Samba'),
                    ('Shopian', 'Shopian'), ('Srinagar', 'Srinagar'), ('Udhampur', 'Udhampur'), ('Bokaro', 'Bokaro'),
                    ('Chatra', 'Chatra'), ('Deoghar', 'Deoghar'), ('Dhanbad', 'Dhanbad'), ('Dumka', 'Dumka'),
                    ('East Singhbhum', 'East Singhbhum'), ('Garhwa', 'Garhwa'), ('Giridih', 'Giridih'),
                    ('Godda', 'Godda'),
                    ('Gumla', 'Gumla'), ('Hazaribag', 'Hazaribag'), ('Jamtara', 'Jamtara'), ('Khunti', 'Khunti'),
                    ('Koderma', 'Koderma'), ('Latehar', 'Latehar'), ('Lohardaga', 'Lohardaga'), ('Pakur', 'Pakur'),
                    ('Palamu', 'Palamu'), ('Ramgarh', 'Ramgarh'), ('Ranchi', 'Ranchi'), ('Sahibganj', 'Sahibganj'),
                    ('Seraikela-Kharsawan', 'Seraikela-Kharsawan'), ('Simdega', 'Simdega'),
                    ('West Singhbhum', 'West Singhbhum'),
                    ('Bagalkot', 'Bagalkot'), ('Ballari (Bellary)', 'Ballari (Bellary)'),
                    ('Belagavi (Belgaum)', 'Belagavi (Belgaum)'),
                    ('Bengaluru (Bangalore) Rural', 'Bengaluru (Bangalore) Rural'),
                    ('Bengaluru (Bangalore) Urban', 'Bengaluru (Bangalore) Urban'), ('Bidar', 'Bidar'),
                    ('Chamarajanagar', 'Chamarajanagar'), ('Chikballapur', 'Chikballapur'),
                    ('Chikkamagaluru (Chikmagalur)', 'Chikkamagaluru (Chikmagalur)'), ('Chitradurga', 'Chitradurga'),
                    ('Dakshina Kannada', 'Dakshina Kannada'), ('Davangere', 'Davangere'), ('Dharwad', 'Dharwad'),
                    ('Gadag', 'Gadag'),
                    ('Hassan', 'Hassan'), ('Haveri', 'Haveri'), ('Kalaburagi (Gulbarga)', 'Kalaburagi (Gulbarga)'),
                    ('Kodagu', 'Kodagu'), ('Kolar', 'Kolar'), ('Koppal', 'Koppal'), ('Mandya', 'Mandya'),
                    ('Mysuru (Mysore)', 'Mysuru (Mysore)'), ('Raichur', 'Raichur'), ('Ramanagara', 'Ramanagara'),
                    ('Shivamogga (Shimoga)', 'Shivamogga (Shimoga)'), ('Tumakuru (Tumkur)', 'Tumakuru (Tumkur)'),
                    ('Udupi', 'Udupi'),
                    ('Uttara Kannada (Karwar)', 'Uttara Kannada (Karwar)'),
                    ('Vijayapura (Bijapur)', 'Vijayapura (Bijapur)'),
                    ('Yadgir', 'Yadgir'), ('Alappuzha', 'Alappuzha'), ('Ernakulam', 'Ernakulam'), ('Idukki', 'Idukki'),
                    ('Kannur', 'Kannur'), ('Kasaragod', 'Kasaragod'), ('Kollam', 'Kollam'), ('Kottayam', 'Kottayam'),
                    ('Kozhikode', 'Kozhikode'), ('Malappuram', 'Malappuram'), ('Palakkad', 'Palakkad'),
                    ('Pathanamthitta', 'Pathanamthitta'), ('Thiruvananthapuram', 'Thiruvananthapuram'),
                    ('Thrissur', 'Thrissur'),
                    ('Wayanad', 'Wayanad'), ('Agatti', 'Agatti'), ('Amini', 'Amini'), ('Androth', 'Androth'),
                    ('Bithra', 'Bithra'),
                    ('Chethlath', 'Chethlath'), ('Kavaratti', 'Kavaratti'), ('Kadmath', 'Kadmath'),
                    ('Kalpeni', 'Kalpeni'),
                    ('Kilthan', 'Kilthan'), ('Minicoy', 'Minicoy'), ('Agar Malwa', 'Agar Malwa'),
                    ('Alirajpur', 'Alirajpur'),
                    ('Anuppur', 'Anuppur'), ('Ashoknagar', 'Ashoknagar'), ('Balaghat', 'Balaghat'),
                    ('Barwani', 'Barwani'),
                    ('Betul', 'Betul'), ('Bhind', 'Bhind'), ('Bhopal', 'Bhopal'), ('Burhanpur', 'Burhanpur'),
                    ('Chhatarpur', 'Chhatarpur'), ('Chhindwara', 'Chhindwara'), ('Damoh', 'Damoh'), ('Datia', 'Datia'),
                    ('Dewas', 'Dewas'), ('Dhar', 'Dhar'), ('Dindori', 'Dindori'), ('Guna', 'Guna'),
                    ('Gwalior', 'Gwalior'),
                    ('Harda', 'Harda'), ('Hoshangabad', 'Hoshangabad'), ('Indore', 'Indore'), ('Jabalpur', 'Jabalpur'),
                    ('Jhabua', 'Jhabua'), ('Katni', 'Katni'), ('Khandwa', 'Khandwa'), ('Khargone', 'Khargone'),
                    ('Mandla', 'Mandla'),
                    ('Mandsaur', 'Mandsaur'), ('Morena', 'Morena'), ('Narsinghpur', 'Narsinghpur'),
                    ('Neemuch', 'Neemuch'),
                    ('Panna', 'Panna'), ('Raisen', 'Raisen'), ('Rajgarh', 'Rajgarh'), ('Ratlam', 'Ratlam'),
                    ('Rewa', 'Rewa'),
                    ('Sagar', 'Sagar'), ('Satna', 'Satna'), ('Sehore', 'Sehore'), ('Seoni', 'Seoni'),
                    ('Shahdol', 'Shahdol'),
                    ('Shajapur', 'Shajapur'), ('Sheopur', 'Sheopur'), ('Shivpuri', 'Shivpuri'), ('Sidhi', 'Sidhi'),
                    ('Singrauli', 'Singrauli'), ('Tikamgarh', 'Tikamgarh'), ('Ujjain', 'Ujjain'), ('Umaria', 'Umaria'),
                    ('Vidisha', 'Vidisha'), ('Ahmednagar', 'Ahmednagar'), ('Akola', 'Akola'), ('Amravati', 'Amravati'),
                    ('Aurangabad', 'Aurangabad'), ('Beed', 'Beed'), ('Bhandara', 'Bhandara'), ('Buldhana', 'Buldhana'),
                    ('Chandrapur', 'Chandrapur'), ('Dhule', 'Dhule'), ('Gadchiroli', 'Gadchiroli'),
                    ('Gondia', 'Gondia'),
                    ('Hingoli', 'Hingoli'), ('Jalgaon', 'Jalgaon'), ('Jalna', 'Jalna'), ('Kolhapur', 'Kolhapur'),
                    ('Latur', 'Latur'),
                    ('Mumbai City', 'Mumbai City'), ('Mumbai Suburban', 'Mumbai Suburban'), ('Nagpur', 'Nagpur'),
                    ('Nanded', 'Nanded'),
                    ('Nandurbar', 'Nandurbar'), ('Nashik', 'Nashik'), ('Osmanabad', 'Osmanabad'),
                    ('Palghar', 'Palghar'),
                    ('Parbhani', 'Parbhani'), ('Pune', 'Pune'), ('Raigad', 'Raigad'), ('Ratnagiri', 'Ratnagiri'),
                    ('Sangli', 'Sangli'),
                    ('Satara', 'Satara'), ('Sindhudurg', 'Sindhudurg'), ('Solapur', 'Solapur'), ('Thane', 'Thane'),
                    ('Wardha', 'Wardha'), ('Washim', 'Washim'), ('Yavatmal', 'Yavatmal'), ('Bishnupur', 'Bishnupur'),
                    ('Chandel', 'Chandel'), ('Churachandpur', 'Churachandpur'), ('Imphal East', 'Imphal East'),
                    ('Imphal West', 'Imphal West'), ('Jiribam', 'Jiribam'), ('Kakching', 'Kakching'),
                    ('Kamjong', 'Kamjong'),
                    ('Kangpokpi', 'Kangpokpi'), ('Noney', 'Noney'), ('Pherzawl', 'Pherzawl'), ('Senapati', 'Senapati'),
                    ('Tamenglong', 'Tamenglong'), ('Tengnoupal', 'Tengnoupal'), ('Thoubal', 'Thoubal'),
                    ('Ukhrul', 'Ukhrul'),
                    ('East Garo Hills', 'East Garo Hills'), ('East Jaintia Hills', 'East Jaintia Hills'),
                    ('East Khasi Hills', 'East Khasi Hills'), ('North Garo Hills', 'North Garo Hills'),
                    ('Ri Bhoi', 'Ri Bhoi'),
                    ('South Garo Hills', 'South Garo Hills'), ('South West Garo Hills ', 'South West Garo Hills '),
                    ('South West Khasi Hills', 'South West Khasi Hills'), ('West Garo Hills', 'West Garo Hills'),
                    ('West Jaintia Hills', 'West Jaintia Hills'), ('West Khasi Hills', 'West Khasi Hills'),
                    ('Aizawl', 'Aizawl'),
                    ('Champhai', 'Champhai'), ('Kolasib', 'Kolasib'), ('Lawngtlai', 'Lawngtlai'),
                    ('Lunglei', 'Lunglei'),
                    ('Mamit', 'Mamit'), ('Saiha', 'Saiha'), ('Serchhip', 'Serchhip'), ('Dimapur', 'Dimapur'),
                    ('Kiphire', 'Kiphire'),
                    ('Kohima', 'Kohima'), ('Longleng', 'Longleng'), ('Mokokchung', 'Mokokchung'), ('Mon', 'Mon'),
                    ('Peren', 'Peren'),
                    ('Phek', 'Phek'), ('Tuensang', 'Tuensang'), ('Wokha', 'Wokha'), ('Zunheboto', 'Zunheboto'),
                    ('Angul', 'Angul'),
                    ('Balangir', 'Balangir'), ('Balasore', 'Balasore'), ('Bargarh', 'Bargarh'), ('Bhadrak', 'Bhadrak'),
                    ('Boudh', 'Boudh'), ('Cuttack', 'Cuttack'), ('Deogarh', 'Deogarh'), ('Dhenkanal', 'Dhenkanal'),
                    ('Gajapati', 'Gajapati'), ('Ganjam', 'Ganjam'), ('Jagatsinghapur', 'Jagatsinghapur'),
                    ('Jajpur', 'Jajpur'),
                    ('Jharsuguda', 'Jharsuguda'), ('Kalahandi', 'Kalahandi'), ('Kandhamal', 'Kandhamal'),
                    ('Kendrapara', 'Kendrapara'),
                    ('Kendujhar (Keonjhar)', 'Kendujhar (Keonjhar)'), ('Khordha', 'Khordha'), ('Koraput', 'Koraput'),
                    ('Malkangiri', 'Malkangiri'), ('Mayurbhanj', 'Mayurbhanj'), ('Nabarangpur', 'Nabarangpur'),
                    ('Nayagarh', 'Nayagarh'), ('Nuapada', 'Nuapada'), ('Puri', 'Puri'), ('Rayagada', 'Rayagada'),
                    ('Sambalpur', 'Sambalpur'), ('Sonepur', 'Sonepur'), ('Sundargarh', 'Sundargarh'),
                    ('Karaikal', 'Karaikal'),
                    ('Mahe', 'Mahe'), ('Pondicherry', 'Pondicherry'), ('Yanam', 'Yanam'), ('Amritsar', 'Amritsar'),
                    ('Barnala', 'Barnala'), ('Bathinda', 'Bathinda'), ('Faridkot', 'Faridkot'),
                    ('Fatehgarh Sahib', 'Fatehgarh Sahib'),
                    ('Fazilka', 'Fazilka'), ('Ferozepur', 'Ferozepur'), ('Gurdaspur', 'Gurdaspur'),
                    ('Hoshiarpur', 'Hoshiarpur'),
                    ('Jalandhar', 'Jalandhar'), ('Kapurthala', 'Kapurthala'), ('Ludhiana', 'Ludhiana'),
                    ('Mansa', 'Mansa'),
                    ('Moga', 'Moga'), ('Muktsar', 'Muktsar'),
                    ('Nawanshahr (Shahid Bhagat Singh Nagar)', 'Nawanshahr (Shahid Bhagat Singh Nagar)'),
                    ('Pathankot', 'Pathankot'),
                    ('Patiala', 'Patiala'), ('Rupnagar', 'Rupnagar'),
                    ('Sahibzada Ajit Singh Nagar (Mohali)', 'Sahibzada Ajit Singh Nagar (Mohali)'),
                    ('Sangrur', 'Sangrur'),
                    ('Tarn Taran', 'Tarn Taran'), ('Ajmer', 'Ajmer'), ('Alwar', 'Alwar'), ('Banswara', 'Banswara'),
                    ('Baran', 'Baran'),
                    ('Barmer', 'Barmer'), ('Bharatpur', 'Bharatpur'), ('Bhilwara', 'Bhilwara'), ('Bikaner', 'Bikaner'),
                    ('Bundi', 'Bundi'), ('Chittorgarh', 'Chittorgarh'), ('Churu', 'Churu'), ('Dausa', 'Dausa'),
                    ('Dholpur', 'Dholpur'),
                    ('Dungarpur', 'Dungarpur'), ('Hanumangarh', 'Hanumangarh'), ('Jaipur', 'Jaipur'),
                    ('Jaisalmer', 'Jaisalmer'),
                    ('Jalore', 'Jalore'), ('Jhalawar', 'Jhalawar'), ('Jhunjhunu', 'Jhunjhunu'), ('Jodhpur', 'Jodhpur'),
                    ('Karauli', 'Karauli'), ('Kota', 'Kota'), ('Nagaur', 'Nagaur'), ('Pali', 'Pali'),
                    ('Pratapgarh', 'Pratapgarh'),
                    ('Rajsamand', 'Rajsamand'), ('Sawai Madhopur', 'Sawai Madhopur'), ('Sikar', 'Sikar'),
                    ('Sirohi', 'Sirohi'),
                    ('Sri Ganganagar', 'Sri Ganganagar'), ('Tonk', 'Tonk'), ('Udaipur', 'Udaipur'),
                    ('East Sikkim', 'East Sikkim'),
                    ('North Sikkim', 'North Sikkim'), ('South Sikkim', 'South Sikkim'), ('West Sikkim', 'West Sikkim'),
                    ('Ariyalur', 'Ariyalur'), ('Chennai', 'Chennai'), ('Coimbatore', 'Coimbatore'),
                    ('Cuddalore', 'Cuddalore'),
                    ('Dharmapuri', 'Dharmapuri'), ('Dindigul', 'Dindigul'), ('Erode', 'Erode'),
                    ('Kanchipuram', 'Kanchipuram'),
                    ('Kanyakumari', 'Kanyakumari'), ('Karur', 'Karur'), ('Krishnagiri', 'Krishnagiri'),
                    ('Madurai', 'Madurai'),
                    ('Nagapattinam', 'Nagapattinam'), ('Namakkal', 'Namakkal'), ('Nilgiris', 'Nilgiris'),
                    ('Perambalur', 'Perambalur'),
                    ('Pudukkottai', 'Pudukkottai'), ('Ramanathapuram', 'Ramanathapuram'), ('Salem', 'Salem'),
                    ('Sivaganga', 'Sivaganga'), ('Thanjavur', 'Thanjavur'), ('Theni', 'Theni'),
                    ('Thoothukudi (Tuticorin)', 'Thoothukudi (Tuticorin)'), ('Tiruchirappalli', 'Tiruchirappalli'),
                    ('Tirunelveli', 'Tirunelveli'), ('Tiruppur', 'Tiruppur'), ('Tiruvallur', 'Tiruvallur'),
                    ('Tiruvannamalai', 'Tiruvannamalai'), ('Tiruvarur', 'Tiruvarur'), ('Vellore', 'Vellore'),
                    ('Viluppuram', 'Viluppuram'), ('Virudhunagar', 'Virudhunagar'), ('Adilabad', 'Adilabad'),
                    ('Bhadradri Kothagudem', 'Bhadradri Kothagudem'), ('Hyderabad', 'Hyderabad'),
                    ('Jagtial', 'Jagtial'),
                    ('Jangaon', 'Jangaon'), ('Jayashankar Bhoopalpally', 'Jayashankar Bhoopalpally'),
                    ('Jogulamba Gadwal', 'Jogulamba Gadwal'), ('Kamareddy', 'Kamareddy'), ('Karimnagar', 'Karimnagar'),
                    ('Khammam', 'Khammam'), ('Komaram Bheem Asifabad', 'Komaram Bheem Asifabad'),
                    ('Mahabubabad', 'Mahabubabad'),
                    ('Mahabubnagar', 'Mahabubnagar'), ('Mancherial', 'Mancherial'), ('Medak', 'Medak'),
                    ('Medchal', 'Medchal'),
                    ('Nagarkurnool', 'Nagarkurnool'), ('Nalgonda', 'Nalgonda'), ('Nirmal', 'Nirmal'),
                    ('Nizamabad', 'Nizamabad'),
                    ('Peddapalli', 'Peddapalli'), ('Rajanna Sircilla', 'Rajanna Sircilla'),
                    ('Rangareddy', 'Rangareddy'),
                    ('Sangareddy', 'Sangareddy'), ('Siddipet', 'Siddipet'), ('Suryapet', 'Suryapet'),
                    ('Vikarabad', 'Vikarabad'),
                    ('Wanaparthy', 'Wanaparthy'), ('Warangal (Rural)', 'Warangal (Rural)'),
                    ('Warangal (Urban)', 'Warangal (Urban)'),
                    ('Yadadri Bhuvanagiri', 'Yadadri Bhuvanagiri'), ('Dhalai', 'Dhalai'), ('Gomati', 'Gomati'),
                    ('Khowai', 'Khowai'),
                    ('North Tripura', 'North Tripura'), ('Sepahijala', 'Sepahijala'),
                    ('South Tripura', 'South Tripura'),
                    ('Unakoti', 'Unakoti'), ('West Tripura', 'West Tripura'), ('Almora', 'Almora'),
                    ('Bageshwar', 'Bageshwar'),
                    ('Chamoli', 'Chamoli'), ('Champawat', 'Champawat'), ('Dehradun', 'Dehradun'),
                    ('Haridwar', 'Haridwar'),
                    ('Nainital', 'Nainital'), ('Pauri Garhwal', 'Pauri Garhwal'), ('Pithoragarh', 'Pithoragarh'),
                    ('Rudraprayag', 'Rudraprayag'), ('Tehri Garhwal', 'Tehri Garhwal'),
                    ('Udham Singh Nagar', 'Udham Singh Nagar'),
                    ('Uttarkashi', 'Uttarkashi'), ('Agra', 'Agra'), ('Aligarh', 'Aligarh'), ('Allahabad', 'Allahabad'),
                    ('Ambedkar Nagar', 'Ambedkar Nagar'),
                    ('Amethi (Chatrapati Sahuji Mahraj Nagar)', 'Amethi (Chatrapati Sahuji Mahraj Nagar)'),
                    ('Amroha (J.P. Nagar)', 'Amroha (J.P. Nagar)'), ('Auraiya', 'Auraiya'), ('Azamgarh', 'Azamgarh'),
                    ('Baghpat', 'Baghpat'), ('Bahraich', 'Bahraich'), ('Ballia', 'Ballia'), ('Balrampur', 'Balrampur'),
                    ('Banda', 'Banda'), ('Barabanki', 'Barabanki'), ('Bareilly', 'Bareilly'), ('Basti', 'Basti'),
                    ('Bhadohi', 'Bhadohi'), ('Bijnor', 'Bijnor'), ('Budaun', 'Budaun'), ('Bulandshahr', 'Bulandshahr'),
                    ('Chandauli', 'Chandauli'), ('Chitrakoot', 'Chitrakoot'), ('Deoria', 'Deoria'), ('Etah', 'Etah'),
                    ('Etawah', 'Etawah'), ('Faizabad', 'Faizabad'), ('Farrukhabad', 'Farrukhabad'),
                    ('Fatehpur', 'Fatehpur'),
                    ('Firozabad', 'Firozabad'), ('Gautam Buddha Nagar', 'Gautam Buddha Nagar'),
                    ('Ghaziabad', 'Ghaziabad'),
                    ('Ghazipur', 'Ghazipur'), ('Gonda', 'Gonda'), ('Gorakhpur', 'Gorakhpur'), ('Hamirpur', 'Hamirpur'),
                    ('Hapur (Panchsheel Nagar)', 'Hapur (Panchsheel Nagar)'), ('Hardoi', 'Hardoi'),
                    ('Hathras', 'Hathras'),
                    ('Jalaun', 'Jalaun'), ('Jaunpur', 'Jaunpur'), ('Jhansi', 'Jhansi'), ('Kannauj', 'Kannauj'),
                    ('Kanpur Dehat', 'Kanpur Dehat'), ('Kanpur Nagar', 'Kanpur Nagar'),
                    ('Kanshiram Nagar (Kasganj)', 'Kanshiram Nagar (Kasganj)'), ('Kaushambi', 'Kaushambi'),
                    ('Kushinagar (Padrauna)', 'Kushinagar (Padrauna)'), ('Lakhimpur - Kheri', 'Lakhimpur - Kheri'),
                    ('Lalitpur', 'Lalitpur'), ('Lucknow', 'Lucknow'), ('Maharajganj', 'Maharajganj'),
                    ('Mahoba', 'Mahoba'),
                    ('Mainpuri', 'Mainpuri'), ('Mathura', 'Mathura'), ('Mau', 'Mau'), ('Meerut', 'Meerut'),
                    ('Mirzapur', 'Mirzapur'),
                    ('Moradabad', 'Moradabad'), ('Muzaffarnagar', 'Muzaffarnagar'), ('Pilibhit', 'Pilibhit'),
                    ('Pratapgarh', 'Pratapgarh'), ('RaeBareli', 'RaeBareli'), ('Rampur', 'Rampur'),
                    ('Saharanpur', 'Saharanpur'),
                    ('Sambhal (Bhim Nagar)', 'Sambhal (Bhim Nagar)'), ('Sant Kabir Nagar', 'Sant Kabir Nagar'),
                    ('Shahjahanpur', 'Shahjahanpur'), ('Shamali (Prabuddh Nagar)', 'Shamali (Prabuddh Nagar)'),
                    ('Shravasti', 'Shravasti'), ('Siddharth Nagar', 'Siddharth Nagar'), ('Sitapur', 'Sitapur'),
                    ('Sonbhadra', 'Sonbhadra'), ('Sultanpur', 'Sultanpur'), ('Unnao', 'Unnao'),
                    ('Varanasi', 'Varanasi'),
                    ('Alipurduar', 'Alipurduar'), ('Bankura', 'Bankura'), ('Birbhum', 'Birbhum'),
                    ('Burdwan (Bardhaman)', 'Burdwan (Bardhaman)'), ('Cooch Behar', 'Cooch Behar'),
                    ('Dakshin Dinajpur (South Dinajpur)', 'Dakshin Dinajpur (South Dinajpur)'),
                    ('Darjeeling', 'Darjeeling'),
                    ('Hooghly', 'Hooghly'), ('Howrah', 'Howrah'), ('Jalpaiguri', 'Jalpaiguri'),
                    ('Kalimpong', 'Kalimpong'),
                    ('Kolkata', 'Kolkata'), ('Malda', 'Malda'), ('Murshidabad', 'Murshidabad'), ('Nadia', 'Nadia'),
                    ('North 24 Parganas', 'North 24 Parganas'),
                    ('Paschim Medinipur (West Medinipur)', 'Paschim Medinipur (West Medinipur)'),
                    ('Purba Medinipur (East Medinipur)', 'Purba Medinipur (East Medinipur)'), ('Purulia', 'Purulia'),
                    ('South 24 Parganas', 'South 24 Parganas'),
                    ('Uttar Dinajpur (North Dinajpur)', 'Uttar Dinajpur (North Dinajpur)')]
    state = models.ForeignKey(AvailableState, related_name="state", on_delete=models.CASCADE)
    district_name = models.CharField(max_length=40, unique=True,choices=district_choices)
    Available_status = models.IntegerField(default=1, blank=True, null=True, help_text='1->Available, 0->Not Available',
                                  choices = (
                                      (1, 'Available'), (0, 'Not Available')
                                  ))

    def __str__(self):
        return self.district_name
