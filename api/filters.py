# filters.py
import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='discount_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='discount_price', lookup_expr='lte')
    digital = django_filters.BooleanFilter(field_name='digital')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'digital']
