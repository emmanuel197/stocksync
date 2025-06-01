from django.contrib import admin
from .models import Brand, Product, Inventory, Location, Order, OrderItem, Supplier, Buyer, Driver, Notification, Communication, Organization
from accounts.models import User

# Register your models here.

admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(Location)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Organization)
admin.site.register(Supplier)
admin.site.register(Buyer)
admin.site.register(Driver)
admin.site.register(Notification)
admin.site.register(Communication)
admin.site.register(User)