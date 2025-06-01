from rest_framework import serializers
from .models import Product, Order, ProductImage, Size, ProductSize, Brand
# class ProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = ('id' ,'name', 'price', 'image', 'description')

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
    
    def get_total_completed_orders(self, obj):  # Add this method
        return obj.get_completed
# class SizeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Size
#         fields = ('name',)

# class ProductSizeSerializer(serializers.ModelSerializer):
#     size = SizeSerializer()

#     class Meta:
#         model = ProductSize
#         fields = ('size',)

# class ProductSerializer(serializers.ModelSerializer):
#     sizes = ProductSizeSerializer(many=True, read_only=True)
#     # other fields...

#     class Meta:
#         model = Product
#         fields = ('id', 'name', 'price', 'image', 'description', 'sizes', 'images')
        

# class ColorSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Color
#         fields = ('name',)

# class OrderItemSerializer(serializers.ModelSerializer):
#     size = SizeSerializer()
#     color = ColorSerializer()

#     class Meta:
#         model = OrderItem
#         fields = ('order', 'product', 'size', 'color', 'quantity', 'date_added', 'get_total')