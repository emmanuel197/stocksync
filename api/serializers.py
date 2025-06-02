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
    images = ProductImageSerializer(many=True, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)
    brand = serializers.SerializerMethodField()
    total_completed_orders = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'discount_price', 'brand', 'image', 'description', 'images', 'sizes', 'total_completed_orders', 'is_available')

    def get_brand(self, obj):
        return obj.brand.name if obj.brand else None  
    
    def get_total_completed_orders(self, obj):
        return obj.get_completed

    def get_is_available(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            user_organization = request.user.organization

            if user_organization and user_organization.organization_type in ['buyer', 'both']:
                accepted_supplier_ids = OrganizationRelationship.objects.filter(
                    buyer_organization=user_organization,
                    status='accepted'
                ).values_list('supplier_organization__id', flat=True)

                total_inventory = Inventory.objects.filter(
                    product=obj,
                    location__organization__id__in=accepted_supplier_ids
                ).aggregate(total_quantity=Sum('quantity'))['total_quantity']

                return total_inventory is not None and total_inventory > 0

            if user_organization and obj.organization == user_organization:
                return True

        return False

class ProductCreateSerializer(serializers.ModelSerializer):
    # Fields that can be written to
    brand = serializers.SlugRelatedField(slug_field='name', queryset=Brand.objects.all(), allow_null=True, required=False)
    # Note: 'organization' will be set automatically in the view

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'discount_price', 'brand', 'image', 'description')
        read_only_fields = ('id',)

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for the Organization model."""
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
    # Organization fields
    name = serializers.CharField(max_length=255)
    logo = serializers.ImageField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)
    contact_email = serializers.EmailField() # Make contact email required for activation
    contact_phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    subscription_plan = serializers.CharField(max_length=50, default='free')
    organization_type = serializers.ChoiceField(
        choices=Organization.ORGANIZATION_TYPE_CHOICES,
        default='buyer' # Default to buyer as per the business plan
    )

    # Initial Admin User fields
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField() # User's login email
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Add custom validation if needed, e.g., check if user email already exists
        if User.objects.filter(email=data['email']).exists():
             raise serializers.ValidationError({"email": "A user with that email already exists."})
        # Validate organization name uniqueness
        if Organization.objects.filter(name=data['name']).exists():
             raise serializers.ValidationError({"name": "An organization with that name already exists."})

        # Validate that password and re_password match
        if data['password'] != data['re_password']:
            raise serializers.ValidationError({"re_password": "Passwords do not match."})

        return data

    def create(self, validated_data):
        # Extract user data
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
        }
        # Pop the re_password field as it's only for validation
        validated_data.pop('re_password')

        # Extract organization type
        organization_type = validated_data.pop('organization_type')

        # Create the Organization (active_status defaults to False in the model)
        organization = Organization.objects.create(organization_type=organization_type, **validated_data)

        # Create the initial Admin User and associate with the organization
        # Use create_user to handle password hashing
        # Generate a username from the email since create_user requires it
        username = user_data['email'].split('@')[0] # Simple username from email prefix

        user = User.objects.create_user(
            username=username, # Provide the generated username
            organization=organization, # Associate user with the organization
            role='admin', # Set the role to admin
            is_active=False, # User should also be inactive until activated
            **user_data
        )

        return {'organization': organization, 'user': user}

class OrganizationRelationshipSerializer(serializers.ModelSerializer):
    # Use SlugRelatedField to represent organizations by their name in read operations
    buyer_organization = serializers.SlugRelatedField(slug_field='name', read_only=True)
    supplier_organization = serializers.SlugRelatedField(slug_field='name', read_only=True)
    initiated_by = serializers.SlugRelatedField(slug_field='email', read_only=True) # Show initiator email

    # Add write-only fields for initiating a relationship
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
        # This create method will be used for initiating a relationship request
        target_organization = validated_data.pop('target_organization_id')
        user = self.context['request'].user # Get the initiating user from the request context
        initiating_organization = user.organization # The organization initiating the request

        # Determine the relationship type based on the initiating organization's type
        if initiating_organization.organization_type in ['buyer', 'both']:
            # Initiating organization is a buyer, applying to be a buyer of the target (supplier)
            buyer_org = initiating_organization
            supplier_org = target_organization
        elif initiating_organization.organization_type in ['supplier', 'both']:
             # Initiating organization is a supplier, applying to be a supplier to the target (buyer)
             buyer_org = target_organization
             supplier_org = initiating_organization
        else:
             raise serializers.ValidationError("Your organization type does not allow initiating relationships.")

        # Check if a relationship already exists
        if OrganizationRelationship.objects.filter(
            buyer_organization=buyer_org,
            supplier_organization=supplier_org
        ).exists():
            raise serializers.ValidationError("A relationship between these organizations already exists.")

        # Create the pending relationship
        relationship = OrganizationRelationship.objects.create(
            buyer_organization=buyer_org,
            supplier_organization=supplier_org,
            status='pending',
            initiated_by=user
        )
        return relationship

    def update(self, instance, validated_data):
        # This update method will be used for accepting/rejecting a relationship
        # Only the 'status' field should be updatable via this serializer
        if 'status' in validated_data:
            instance.status = validated_data['status']
            instance.save(update_fields=['status', 'updated_at'])
            return instance
        else:
            pass

        return instance

# Add a serializer for listing potential suppliers
class PotentialSupplierSerializer(serializers.ModelSerializer):
    """Serializer for listing potential supplier organizations."""
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'logo', 'address', 'contact_email',
            'contact_phone', 'organization_type'
        ]

class BuyerSerializer(serializers.ModelSerializer):
    # Add fields for the associated user
    user_email = serializers.EmailField(write_only=True)
    user_password = serializers.CharField(write_only=True)
    user_first_name = serializers.CharField(max_length=150, write_only=True)
    user_last_name = serializers.CharField(max_length=150, write_only=True)
    user_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True, write_only=True)

    class Meta:
        model = Buyer
        fields = '__all__'
        read_only_fields = ('organization', 'buyer_code', 'created_at', 'updated_at') # organization will be set by view

    def validate_user_email(self, value):
        # Validate that the user email is unique
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

class SupplierSerializer(serializers.ModelSerializer):
    # Add fields for the associated user
    user_email = serializers.EmailField(write_only=True)
    user_password = serializers.CharField(write_only=True)
    user_first_name = serializers.CharField(max_length=150, write_only=True)
    user_last_name = serializers.CharField(max_length=150, write_only=True)
    user_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True, write_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ('organization', 'supplier_code', 'created_at', 'updated_at') # organization will be set by view

    def validate_user_email(self, value):
        # Validate that the user email is unique
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

class DriverSerializer(serializers.ModelSerializer):
    # Add fields for the associated user
    user_email = serializers.EmailField(write_only=True)
    user_password = serializers.CharField(write_only=True)
    user_first_name = serializers.CharField(max_length=150, write_only=True)
    user_last_name = serializers.CharField(max_length=150, write_only=True)
    user_phone_number = serializers.CharField(max_length=20, required=False, allow_null=True, write_only=True)

    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ('organization', 'created_at', 'updated_at') # organization will be set by view

    def validate_user_email(self, value):
        # Validate that the user email is unique
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

class InventorySerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True) # Include product details
    location = serializers.SlugRelatedField(slug_field='name', read_only=True) # Show location name

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'location', 'quantity', 'last_stocked',
            'last_sold', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'last_stocked', 'last_sold', 'created_at', 'updated_at'
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.get('context', {}).get('request')
        super().__init__(*args, **kwargs)

        if request and request.user and request.user.is_authenticated:
            user_organization = request.user.organization
            if user_organization and user_organization.organization_type in ['buyer', 'both']:
                self.fields.pop('quantity', None)
        elif request and (not request.user or not request.user.is_authenticated or not request.user.organization):
            self.fields.pop('quantity', None)

class InventoryCreateSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for product and location to allow writing their IDs
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'location', 'quantity'
        ]
        read_only_fields = ('id',)

    def validate(self, data):
        # Ensure the product and location belong to the authenticated user's organization
        request = self.context.get('request')
        user_organization = request.user.organization

        product = data.get('product')
        location = data.get('location')

        if product and product.organization != user_organization:
            raise serializers.ValidationError({"product": "You can only add inventory for products belonging to your organization."})

        if location and location.organization != user_organization:
            raise serializers.ValidationError({"location": "You can only add inventory to locations belonging to your organization."})

        # Check if an inventory item for this product and location already exists
        if Inventory.objects.filter(product=product, location=location).exists():
             raise serializers.ValidationError({"non_field_errors": "Inventory for this product at this location already exists. Consider updating the existing item."})

        return data

class InventoryMovementSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer(read_only=True, context={'request': None})
    moved_by = serializers.SlugRelatedField(slug_field='email', read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'inventory', 'movement_type', 'quantity_changed',
            'timestamp', 'moved_by'
        ]
        read_only_fields = [
            'timestamp', 'moved_by'
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.get('context', {}).get('request')
        super().__init__(*args, **kwargs)

        if 'inventory' in self.fields:
            self.fields['inventory'].context['request'] = request

# Modified BrandSerializer
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']
        read_only_fields = []

# Modified CategorySerializer
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