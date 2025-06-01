from rest_framework import serializers
from .models import Product, Order, ProductImage, Size, ProductSize, Brand, OrderItem, ShippingAddress, Buyer, Supplier, Driver, Category, Location, Inventory, InventoryMovement
from accounts.models import Organization, User

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

    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'discount_price', 'brand', 'image', 'description', 'images', 'sizes', 'total_completed_orders')

    def get_brand(self, obj):
        return obj.brand.name if obj.brand else None  
    
    def get_total_completed_orders(self, obj):
        return obj.get_completed

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        model = Organization
        fields = '__all__'
        read_only_fields = ('active_status', 'email_sent', 'created_at', 'updated_at')

class OrganizationOnboardingSerializer(serializers.Serializer):
    # Organization fields
    name = serializers.CharField(max_length=255)
    logo = serializers.ImageField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)
    contact_email = serializers.EmailField() # Make contact email required for activation
    contact_phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    subscription_plan = serializers.CharField(max_length=50, default='free')

    # Initial Admin User fields
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField() # User's login email
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Add custom validation if needed, e.g., check if user email already exists
        if User.objects.filter(email=data['email']).exists():
             raise serializers.ValidationError({"email": "A user with that email already exists."})
        # You might also want to validate organization name uniqueness here if needed,
        # although the model has unique=True, validating here provides a better API error response.
        if Organization.objects.filter(name=data['name']).exists():
             raise serializers.ValidationError({"name": "An organization with that name already exists."})
        return data

    def create(self, validated_data):
        # Extract user data
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
        }

        # Create the Organization (active_status defaults to False in the model)
        organization = Organization.objects.create(**validated_data)

        # Create the initial Admin User and associate with the organization
        # Use create_user to handle password hashing
        # Generate a username from the email since create_user requires it
        username = user_data['email'].split('@')[0] # Simple username from email prefix
        # Ensure username is unique if necessary, though email is unique
        # If your User model requires a unique username, you might need more robust generation or validation.

        user = User.objects.create_user(
            username=username, # Provide the generated username
            organization=organization, # Associate user with the organization
            role='admin', # Set the role to admin
            is_active=False, # User should also be inactive until activated by Djoser
            **user_data
        )

        # We don't send the custom organization email here anymore.
        # Djoser's user activation email will be triggered by the view.

        return {'organization': organization, 'user': user}

class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'