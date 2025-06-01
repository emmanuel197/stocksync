from django.db import models
from accounts.models import User
import random, string

# Create your models here.


class Customer(models.Model):
    customer_id = models.CharField(max_length=200, null=True, blank=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200, null=True, blank=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=200, null=True, blank=True)

    
class Brand(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
    

   
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    discount_price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    digital = models.BooleanField(default=False, null=True, blank=True)
    image = models.ImageField(upload_to='images/' ,null=True, blank=True)
    description = models.TextField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return self.name
    
    @property
    def get_completed(self):
        return self.orderitem_set.filter(order__complete=True).count()
class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    
class ProductSize(models.Model):
    product = models.ForeignKey(Product, related_name='sizes', on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f'{self.product.name} - {self.size.name}'

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    color = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images/variants/')
    default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.product.name} - {self.color}'   
def generate_unique_transaction_id():
    length= 6
    while True:
        transaction_id = ''.join(random.choices(string.ascii_uppercase, k=length))
        if Order.objects.filter(transaction_id=transaction_id).count() == 0:
            break
    return transaction_id
class Order(models.Model):
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    transaction_id = models.CharField(default=generate_unique_transaction_id, max_length=8, unique=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    date_completed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.transaction_id
    
    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total


    
    @property
    def shipping(self):
        shipping = False
        all_digital = all([item.product.digital for item in self.orderitem_set.all()])
        if not all_digital:
            shipping = True
        return shipping

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total
    

class ShippingAddress(models.Model): 
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE) 
    order = models.ForeignKey(Order, on_delete=models.CASCADE) 
    address = models.CharField(max_length=200) 
    city = models.CharField(max_length=200) 
    state = models.CharField(max_length=200) 
    zipcode = models.CharField(max_length=200)
    country = models.CharField(max_length=200) 
    date_added = models.DateTimeField(auto_now_add=True)

