from django.contrib import admin
from .models import *
from accounts.models import User


admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(ShippingAddress)
admin.site.register(OrderItem)
admin.site.register(Product)
admin.site.register(User)
admin.site.register(Brand)
admin.site.register(Size)
admin.site.register(ProductSize)
admin.site.register(ProductImage)