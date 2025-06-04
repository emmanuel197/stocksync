from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, Q, Prefetch
import uuid
from accounts.models import User, Organization
from decimal import Decimal
import random, string
from django.utils import timezone
from django.db import transaction

# Create your models here.


class Brand(models.Model):
    name = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='brands')

    def __str__(self):
        return self.name


class Supplier(models.Model):
    PAYMENT_TERMS_CHOICES = [
        ('immediate', 'Immediate'),
        ('net_15', 'Net 15 Days'),
        ('net_30', 'Net 30 Days'),
        ('net_45', 'Net 45 Days'),
        ('net_60', 'Net 60 Days'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    supplier_code = models.CharField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='net_30')
    active_status = models.BooleanField(default=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='suppliers')
    notes = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['supplier_code']),
            models.Index(fields=['organization']),
            models.Index(fields=['active_status']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Generate supplier code if not set
        if not self.supplier_code:
            prefix = 'SUP'
            if self.organization:
                last_supplier = Supplier.objects.base_manager.filter(organization=self.organization).order_by('-id').first()
                if last_supplier and last_supplier.supplier_code.startswith(prefix):
                    try:
                        last_number = int(last_supplier.supplier_code[len(prefix):])
                        self.supplier_code = f"{prefix}{last_number + 1:04d}"
                    except ValueError:
                        self.supplier_code = f"{prefix}0001"
                else:
                    self.supplier_code = f"{prefix}0001"
            else:
                self.supplier_code = f"{prefix}0001"

        super().save(*args, **kwargs)

    def get_order_history(self):
        """Get purchase order history from this supplier"""
        pass

    def get_performance_metrics(self):
        """Calculate supplier performance metrics"""
        return {
            'total_orders': 0,
            'on_time_delivery_rate': 0,
            'quality_rating': 0,
        }


class Buyer(models.Model):
    PAYMENT_TERMS_CHOICES = [
        ('prepaid', 'Prepaid'),
        ('cod', 'Cash on Delivery'),
        ('net_15', 'Net 15 Days'),
        ('net_30', 'Net 30 Days'),
        ('custom', 'Custom'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_profile', null=True, blank=True)  # Add null=True, blank=True
    organization = models.ForeignKey('accounts.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='buyers')
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=200)
    buyer_code = models.CharField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES, default='prepaid')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    active_status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['buyer_code']),
            models.Index(fields=['organization']),
            models.Index(fields=['active_status']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Generate buyer code if not set
        if not self.buyer_code:
            prefix = 'BUY'
            if self.organization:
                last_buyer = Buyer.objects.base_manager.filter(organization=self.organization).order_by('-id').first()
                if last_buyer and last_buyer.buyer_code.startswith(prefix):
                    try:
                        last_number = int(last_buyer.buyer_code[len(prefix):])
                        self.buyer_code = f"{prefix}{last_number + 1:04d}"
                    except ValueError:
                        self.buyer_code = f"{prefix}0001"
                else:
                    self.buyer_code = f"{prefix}0001"
            else:
                self.buyer_code = f"{prefix}0001"

        super().save(*args, **kwargs)

    def get_order_history(self):
        """Get order history from this buyer"""
        return self.orders.all()

    def get_current_credit_usage(self):
        """Calculate current credit usage"""
        unpaid_orders = self.orders.filter(
            payment_status__in=['unpaid', 'partially_paid']
        )
        return sum(order.total_amount for order in unpaid_orders)

    def has_available_credit(self, amount):
        """Check if buyer has available credit for an order"""
        current_usage = self.get_current_credit_usage()
        return (current_usage + amount) <= self.credit_limit


class Driver(models.Model):
    name = models.CharField(max_length=200)
    contact_info = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    vehicle_details = models.TextField(blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    active_status = models.BooleanField(default=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='drivers')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['license_number']),
            models.Index(fields=['organization']),
            models.Index(fields=['active_status']),
        ]

    def __str__(self):
        return self.name

    def get_delivery_history(self):
        """Get delivery history for this driver"""
        pass


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['organization']),
        ]
        unique_together = ['name', 'organization']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost price per unit")
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    digital = models.BooleanField(default=False, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='products')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['organization']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return self.name

    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost is not None and self.price is not None and self.price > 0:
            return ((self.price - self.cost) / self.price) * 100
        return None

    @property
    def total_inventory(self):
        """Get total inventory quantity across all locations"""
        return self.inventory_items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def get_completed(self):
        """Calculates the total quantity of this product in completed orders."""
        total = self.order_items.filter(order__status='delivered').aggregate(Sum('quantity'))['quantity__sum']
        return total if total is not None else 0


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


class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='locations')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['organization']),
        ]
        unique_together = ['name', 'organization']

    def __str__(self):
        return self.name


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.IntegerField(default=5, help_text="Minimum stock level before alert is triggered")
    max_stock_level = models.IntegerField(default=100, help_text="Maximum stock level")
    last_stocked = models.DateTimeField(auto_now=True)
    last_sold = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='inventory', null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Inventory Items'
        unique_together = ['product', 'location']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['location']),
            models.Index(fields=['organization']),
            models.Index(fields=['quantity']),
        ]

    def __str__(self):
        return f"{self.product.name} at {self.location.name}: {self.quantity} units"

    @property
    def is_low_stock(self):
        """Check if inventory is below minimum stock level"""
        return self.quantity <= self.min_stock_level

    @property
    def is_overstock(self):
        """Check if inventory exceeds maximum stock level"""
        return self.quantity >= self.max_stock_level

    @property
    def stock_value(self):
        """Calculate total value of inventory"""
        return Decimal(self.quantity) * self.product.cost

    def add_stock(self, amount, note=None):
        """Add stock to inventory"""
        self.quantity += amount
        self.save()
        InventoryMovement.objects.create(
            inventory=self,
            quantity_change=amount,
            movement_type='addition',
            note=note or f"Added {amount} units"
        )
        return True

    def remove_stock(self, amount, note=None):
        """Remove stock from inventory"""
        if self.quantity >= amount:
            self.quantity -= amount
            self.save()
            InventoryMovement.objects.create(
                inventory=self,
                quantity_change=-amount,
                movement_type='removal',
                note=note or f"Removed {amount} units"
            )
            return True
        return False


class InventoryMovement(models.Model):
    MOVEMENT_TYPES = [
        ('addition', 'Stock Added'),
        ('removal', 'Stock Removed'),
        ('adjustment', 'Stock Adjusted'),
        ('transfer', 'Stock Transferred'),
    ]

    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='movements')
    quantity_change = models.IntegerField(help_text="Positive for additions, negative for removals")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    note = models.TextField(blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Reference to order, transfer, etc.")
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['inventory']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['organization']),
        ]

    def __str__(self):
        return f"{self.movement_type}: {self.quantity_change} units of {self.inventory.product.name}"


def generate_unique_transaction_id():
    length = 6
    while True:
        transaction_id = ''.join(random.choices(string.ascii_uppercase, k=length))
        if Order.objects.filter(transaction_id=transaction_id).count() == 0:
            break
    return transaction_id


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    order_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey('Buyer', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    shipping_address = models.TextField(blank=True, null=True)
    customer_info = models.JSONField(blank=True, null=True, help_text="Additional customer information")
    notes = models.TextField(blank=True, null=True)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_orders')
    updated_at = models.DateTimeField(auto_now=True)
    date_completed = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
            models.Index(fields=['organization']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return self.order_number if self.order_number else f"Order (ID: {self.id or 'N/A'})"

    def save(self, *args, **kwargs):
        if not self.order_number and self.organization:
            prefix = 'ORD'
            with transaction.atomic():
                last_order = Order.objects.filter(organization=self.organization).select_for_update().order_by('-id').first()
                if last_order and last_order.order_number:
                    try:
                        parts = last_order.order_number.split('-')
                        if len(parts) > 2:
                            last_number = int(parts[-1])
                            new_number = last_number + 1
                            self.order_number = f'{prefix}-{self.organization.id}-{new_number:06d}'
                        else:
                            self.order_number = f'{prefix}-{self.organization.id}-000001'
                    except (ValueError, IndexError):
                        self.order_number = f'{prefix}-{self.organization.id}-000001'
                else:
                    self.order_number = f'{prefix}-{self.organization.id}-000001'
        elif not self.order_number:
            pass

        super().save(*args, **kwargs)

    def calculate_total(self):
        return self.items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')

    def update_inventory(self, add_to_inventory=False):
        for item in self.items.all():
            product = item.product
            try:
                default_location = Location.objects.filter(organization=self.organization).first()
                if default_location:
                    inventory, created = Inventory.objects.get_or_create(
                        product=product,
                        location=default_location,
                        organization=self.organization,
                        defaults={'quantity': 0}
                    )

                    if add_to_inventory:
                        inventory.add_stock(
                            item.quantity,
                            f"Order {self.order_number} canceled/returned"
                        )
                    else:
                        inventory.remove_stock(
                            item.quantity,
                            f"Order {self.order_number}"
                        )
            except Exception as e:
                print(f"Error updating inventory for order {self.order_number}: {e}")

    @property
    def get_cart_total(self):
        total = self.items.aggregate(total=Sum('subtotal'))['total']
        return total if total is not None else Decimal('0.00')

    @property
    def get_cart_items(self):
        total_quantity = self.items.aggregate(total_quantity=Sum('quantity'))['total_quantity']
        return total_quantity if total_quantity is not None else 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    organization = models.ForeignKey('accounts.Organization', on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
            models.Index(fields=['organization']),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.order_number if self.order and self.order.order_number else 'N/A'}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price

        super().save(*args, **kwargs)

        self.order.refresh_from_db()
        self.order.total_amount = self.order.get_cart_total
        self.order.save()

    @property
    def get_total(self):
        """
        Calculates the total price for this order item (quantity * unit_price).
        This is equivalent to the 'subtotal' field.
        """
        return self.subtotal


class ShippingAddress(models.Model):
    customer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('low_stock', 'Low Stock Alert'),
        ('order', 'Order Update'),
        ('system', 'System Message'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    read_status = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of related object (e.g., 'order', 'product')")
    related_object_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of related object")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notifications')

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['read_status']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['organization']),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.email}: {self.message[:50]}"

    def mark_as_read(self):
        self.read_status = True
        self.save()

    @classmethod
    def get_unread_count(cls, user):
        return cls.objects.filter(user=user, read_status=False).count()

    @classmethod
    def create_low_stock_notification(cls, inventory, user=None):
        if not user:
            users = User.objects.filter(
                organization=inventory.organization,
                role__in=['admin', 'manager'],
                is_active=True
            )
        else:
            users = [user]

        notifications = []
        message = f"Low stock alert: {inventory.product.name} at {inventory.location.name} is below minimum level. Current: {inventory.quantity}, Minimum: {inventory.min_stock_level}"

        for user in users:
            notification = cls.objects.create(
                user=user,
                message=message,
                notification_type='low_stock',
                related_object_type='inventory',
                related_object_id=inventory.id,
                organization=inventory.organization
            )
            notifications.append(notification)

        return notifications


class Communication(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_communications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_communications')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_status = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='communication_attachments/', null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='communications')

    class Meta:
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['recipient']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['read_status']),
            models.Index(fields=['organization']),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.email} to {self.recipient.email}: {self.message[:50]}"

    def mark_as_read(self):
        self.read_status = True
        self.save()

    @classmethod
    def get_unread_count(cls, user):
        return cls.objects.filter(recipient=user, read_status=False).count()

