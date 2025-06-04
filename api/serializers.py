from rest_framework import serializers
from .models import Product, Order, ProductImage, Size, ProductSize, Brand, OrderItem, ShippingAddress, Buyer, Supplier, Driver, Category, Location, Inventory, InventoryMovement
from accounts.models import Organization, User, OrganizationRelationship
from django.db import transaction
from django.db.models import Sum

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('color', 'image', 'default')

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ('name',)

class ProductSizeSerializer(serializers.ModelSerializer):
    size = SizeSerializer()

    class Meta:
        model = ProductSize
        fields = ('size',)

class ProductSerializer(serializers.ModelSerializer):
    """
    Standard Serializer for the Product model.
    Includes all fields, including 'cost'. Used for suppliers/internal users.
    """
    category = serializers.SlugRelatedField(slug_field='name', read_only=True)
    brand = serializers.SlugRelatedField(slug_field='name', read_only=True)
    images = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    total_completed_orders = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'category', 'brand', 'price',
            'cost', 'image', 'barcode', 'digital', 'organization', 'active',
            'created_at', 'updated_at', 'images', 'sizes', 'total_completed_orders', 'is_available'
        ]
        read_only_fields = ['organization', 'created_at', 'updated_at', 'images', 'sizes', 'total_completed_orders', 'is_available']

    def get_images(self, obj):
        request = self.context.get('request')
        images = ProductImage.objects.filter(product=obj)
        try:
            return ProductImageSerializer(images, many=True, context={'request': request}).data
        except ImportError:
            return []

    def get_sizes(self, obj):
        sizes = ProductSize.objects.filter(product=obj)
        try:
            return ProductSizeSerializer(sizes, many=True).data
        except ImportError:
            return []

    def get_total_completed_orders(self, obj):
        return obj.get_completed

    def get_is_available(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            user_organization = request.user.organization

            if user_organization:
                if obj.organization == user_organization:
                     total_inventory = Inventory.objects.filter(
                         product=obj,
                         organization=user_organization
                     ).aggregate(total_quantity=Sum('quantity'))['total_quantity']
                     return total_inventory is not None and total_inventory > 0

                if user_organization.organization_type in ['buyer', 'both']:
                    is_accepted_supplier = OrganizationRelationship.objects.filter(
                        buyer_organization=user_organization,
                        supplier_organization=obj.organization,
                        status='accepted'
                    ).exists()

                    if is_accepted_supplier:
                        total_inventory = Inventory.objects.filter(
                            product=obj,
                            organization=obj.organization
                        ).aggregate(total_quantity=Sum('quantity'))['total_quantity']

                        return total_inventory is not None and total_inventory > 0

        return False

class BuyerSupplierProductSerializer(serializers.ModelSerializer):
    """
    Serializer for buyers viewing supplier products.
    Excludes sensitive fields like 'cost'.
    """
    category = serializers.SlugRelatedField(slug_field='name', read_only=True)
    brand = serializers.SlugRelatedField(slug_field='name', read_only=True)
    images = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    total_completed_orders = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'category', 'brand', 'price',
            'image', 'barcode', 'digital', 'organization', 'active',
            'created_at', 'updated_at', 'images', 'sizes', 'total_completed_orders', 'is_available'
        ]
        read_only_fields = ['organization', 'created_at', 'updated_at', 'images', 'sizes', 'total_completed_orders', 'is_available']

    def get_images(self, obj):
        request = self.context.get('request')
        images = ProductImage.objects.filter(product=obj)
        try:
            return ProductImageSerializer(images, many=True, context={'request': request}).data
        except ImportError:
            return []

    def get_sizes(self, obj):
        sizes = ProductSize.objects.filter(product=obj)
        try:
            return ProductSizeSerializer(sizes, many=True).data
        except ImportError:
            return []

    def get_total_completed_orders(self, obj):
        return obj.get_completed

    def get_is_available(self, obj):
        print(f"--- get_is_available for Product ID: {obj.id} ---")
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            print(f"User authenticated: {request.user.email}")
            user_organization = request.user.organization
            print(f"User Organization: {user_organization.id if user_organization else 'None'}")

            if user_organization:
                if user_organization.organization_type in ['buyer', 'both']:
                    print(f"User organization type is buyer/both: {user_organization.organization_type}")
                    print(f"Checking relationship between Buyer Org {user_organization.id} and Supplier Org {obj.organization.id}")
                    is_accepted_supplier = OrganizationRelationship.objects.filter(
                        buyer_organization=user_organization,
                        supplier_organization=obj.organization,
                        status='accepted'
                    ).exists()
                    print(f"Is accepted supplier relationship exists: {is_accepted_supplier}")

                    if is_accepted_supplier:
                        print(f"Calculating total inventory for Product ID {obj.id} in Organization ID {obj.organization.id}")
                        total_inventory = Inventory.objects.filter(
                            product=obj,
                            organization=obj.organization
                        ).aggregate(total_quantity=Sum('quantity'))['total_quantity']
                        print(f"Total inventory calculated: {total_inventory}")

                        result = total_inventory is not None and total_inventory > 0
                        print(f"Final is_available result: {result}")
                        print("--- End get_is_available ---")
                        return result
                    else:
                        print("No accepted supplier relationship found.")

        print("Conditions not met for availability check.")
        print("--- End get_is_available ---")
        return False

class ProductCreateSerializer(serializers.ModelSerializer):
    cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), allow_null=True, required=False)
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'category', 'brand', 'price',
            'cost', 'image', 'barcode', 'digital', 'active'
        ]
        read_only_fields = ('id',)

    def validate_sku(self, value):
        request = self.context.get('request')
        user_organization = request.user.organization
        queryset = Product.objects.filter(sku=value, organization=user_organization)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("A product with this SKU already exists in your organization.")
        return value

    def validate_category(self, value):
        request = self.context.get('request')
        user_organization = request.user.organization
        if value and value.organization != user_organization:
            raise serializers.ValidationError("You can only assign categories belonging to your organization.")
        return value

    def validate_brand(self, value):
        request = self.context.get('request')
        user_organization = request.user.organization
        if value and value.organization != user_organization:
            raise serializers.ValidationError("You can only assign brands belonging to your organization.")
        return value

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'logo', 'address', 'contact_email',
            'contact_phone', 'subscription_plan', 'organization_type',
            'active_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'subscription_plan', 'active_status', 'created_at', 'updated_at'
        ]

class OrganizationOnboardingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    logo = serializers.ImageField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    subscription_plan = serializers.CharField(max_length=50, default='free')
    organization_type = serializers.ChoiceField(
        choices=Organization.ORGANIZATION_TYPE_CHOICES,
        default='buyer'
    )

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
             raise serializers.ValidationError({"email": "A user with that email already exists."})
        if Organization.objects.filter(name=data['name']).exists():
             raise serializers.ValidationError({"name": "An organization with that name already exists."})

        if data['password'] != data['re_password']:
            raise serializers.ValidationError({"re_password": "Passwords do not match."})

        return data

    def create(self, validated_data):
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
        }
        validated_data.pop('re_password')

        organization_type = validated_data.pop('organization_type')

        organization = Organization.objects.create(organization_type=organization_type, **validated_data)

        username = user_data['email'].split('@')[0]

        user = User.objects.create_user(
            username=username,
            organization=organization,
            role='admin',
            is_active=False,
            **user_data
        )

        return {'organization': organization, 'user': user}

class OrganizationRelationshipSerializer(serializers.ModelSerializer):
    buyer_organization = serializers.SlugRelatedField(slug_field='name', read_only=True)
    supplier_organization = serializers.SlugRelatedField(slug_field='name', read_only=True)
    initiated_by = serializers.SlugRelatedField(slug_field='email', read_only=True)

    target_organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), write_only=True, label="Target Organization ID"
    )

    class Meta:
        model = OrganizationRelationship
        fields = [
            'id', 'buyer_organization', 'supplier_organization', 'status',
            'initiated_by', 'created_at', 'updated_at', 'target_organization_id'
        ]
        read_only_fields = ['initiated_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        target_organization = validated_data.pop('target_organization_id')
        user = self.context['request'].user
        initiating_organization = user.organization

        if initiating_organization.organization_type in ['buyer', 'both']:
            buyer_org = initiating_organization
            supplier_org = target_organization
        elif initiating_organization.organization_type in ['supplier', 'both']:
             buyer_org = target_organization
             supplier_org = initiating_organization
        else:
             raise serializers.ValidationError("Your organization type does not allow initiating relationships.")

        if OrganizationRelationship.objects.filter(
            buyer_organization=buyer_org,
            supplier_organization=supplier_org
        ).exists():
            raise serializers.ValidationError("A relationship between these organizations already exists.")

        relationship = OrganizationRelationship.objects.create(
            buyer_organization=buyer_org,
            supplier_organization=supplier_org,
            status='pending',
            initiated_by=user
        )
        return relationship

    def update(self, instance, validated_data):
        if 'status' in validated_data:
            instance.status = validated_data['status']
            instance.save(update_fields=['status', 'updated_at'])
            return instance
        else:
            pass

        return instance

class PotentialSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'logo', 'address', 'contact_email',
            'contact_phone', 'organization_type'
        ]

class BuyerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)
    user_password = serializers.CharField(write_only=True)
    user_first_name = serializers.CharField(max_length=150, write_only=True)
    user_last_name = serializers.CharField(max_length=150, write_only=True)
    user_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True, write_only=True)

    class Meta:
        model = Buyer
        fields = '__all__'
        read_only_fields = ('organization', 'buyer_code', 'created_at', 'updated_at')

    def validate_user_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

class SupplierSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)
    user_password = serializers.CharField(write_only=True)
    user_first_name = serializers.CharField(max_length=150, write_only=True)
    user_last_name = serializers.CharField(max_length=150, write_only=True)
    user_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True, write_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ('organization', 'supplier_code', 'created_at', 'updated_at')

    def validate_user_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

class DriverSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)
    user_password = serializers.CharField(write_only=True)
    user_first_name = serializers.CharField(max_length=150, write_only=True)
    user_last_name = serializers.CharField(max_length=150, write_only=True)
    user_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True, write_only=True)

    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ('organization', 'created_at', 'updated_at')

    def validate_user_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        request = self.context.get('request')
        user_organization = request.user.organization
        name = data.get('name')

        queryset = Location.objects.filter(name=name, organization=user_organization)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({"name": "A location with this name already exists in your organization."})

        return data

class InventorySerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'location', 'quantity', 'last_stocked', 'last_sold',
            'created_at', 'updated_at', 'organization'
        ]
        read_only_fields = ['last_stocked', 'last_sold', 'created_at', 'updated_at', 'organization']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        user_organization = request.user.organization if request and request.user and request.user.is_authenticated else None

        # Check if the user is a buyer/both and the product belongs to a different organization
        if user_organization and user_organization.organization_type in ['buyer', 'both'] and instance.product.organization != user_organization:
            # If it's a supplier's product viewed by a buyer, use BuyerSupplierProductSerializer for the product part
            product_serializer = BuyerSupplierProductSerializer(instance.product, context=self.context)
            representation['product'] = product_serializer.data
            # Keep quantity as it's in the buyer's inventory
        else:
            # Otherwise, use the standard ProductSerializer (shows cost)
            product_serializer = ProductSerializer(instance.product, context=self.context)
            representation['product'] = product_serializer.data
            # Keep quantity

        return representation

class BuyerSupplierInventorySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    is_available = serializers.SerializerMethodField()
    product = BuyerSupplierProductSerializer(read_only=True) # Use the buyer-specific product serializer

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'location', 'is_available', 'last_stocked', # Include product, exclude quantity
            'created_at', 'updated_at', 'organization'
        ]
        read_only_fields = ['last_stocked', 'created_at', 'updated_at', 'organization']

    def get_is_available(self, obj):
        return obj.quantity > 0

class InventoryCreateSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'location', 'quantity'
        ]
        read_only_fields = ('id',)

    def validate(self, data):
        request = self.context.get('request')
        user_organization = request.user.organization

        product = data.get('product')
        location = data.get('location')

        if product and product.organization != user_organization:
            raise serializers.ValidationError({"product": "You can only add inventory for products belonging to your organization."})

        if location and location.organization != user_organization:
            raise serializers.ValidationError({"location": "You can only add inventory to locations belonging to your organization."})

        if Inventory.objects.filter(product=product, location=location).exists():
             raise serializers.ValidationError({"non_field_errors": "Inventory for this product at this location already exists. Consider updating the existing item."})

        return data

class InventoryMovementSerializer(serializers.ModelSerializer):
    inventory = serializers.SerializerMethodField()
    moved_by = serializers.SlugRelatedField(slug_field='email', read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'inventory', 'movement_type', 'quantity_change',
            'timestamp', 'moved_by'
        ]
        read_only_fields = [
            'timestamp', 'moved_by'
        ]

    def get_inventory(self, obj):
        request = self.context.get('request')
        user_organization = request.user.organization if request and request.user and request.user.is_authenticated else None

        # Re-fetch the Inventory object to ensure we have the latest quantity
        try:
            inventory_item = Inventory.objects.get(pk=obj.inventory.pk)
        except Inventory.DoesNotExist:
            return None # Or handle this case as appropriate

        product_organization = inventory_item.product.organization

        # If the user is a buyer/both AND the product belongs to a different organization (a supplier)
        # Use BuyerSupplierInventorySerializer which hides quantity and uses BuyerSupplierProductSerializer
        if user_organization and user_organization.organization_type in ['buyer', 'both'] and product_organization != user_organization:
            # Note: BuyerSupplierInventorySerializer excludes 'quantity' by design
            return BuyerSupplierInventorySerializer(inventory_item, context=self.context).data
        else:
            # Otherwise (user is supplier/internal, or buyer viewing their own product,
            # or buyer viewing a supplier product that is somehow in their own inventory),
            # use the standard InventorySerializer.
            # InventorySerializer's to_representation already handles hiding cost for supplier products in buyer's inventory.
            return InventorySerializer(inventory_item, context=self.context).data

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']
        read_only_fields = []

class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), allow_null=True, required=False
    )
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'parent_name']
        read_only_fields = []

    def validate(self, data):
        request = self.context.get('request')
        user_organization = request.user.organization
        name = data.get('name')
        parent = data.get('parent')

        queryset = Category.objects.filter(name=name, organization=user_organization)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({"name": "A category with this name already exists in your organization."})

        if self.instance and parent and self.instance.pk == parent.pk:
             raise serializers.ValidationError({"parent": "A category cannot be its own parent."})

        return data

class OrderItemSerializer(serializers.ModelSerializer):
    product = BuyerSupplierProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'quantity', 'unit_price', 'subtotal',
        ]
        read_only_fields = ['subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer = serializers.SlugRelatedField(slug_field='email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'organization', 'status',
            'total_amount', 'order_date', 'shipping_address', 'notes',
            'payment_status', 'created_by', 'updated_at',
            'items'
        ]
        read_only_fields = [
            'order_number', 'organization', 'status', 'total_amount',
            'order_date', 'created_by', 'updated_at'
        ]