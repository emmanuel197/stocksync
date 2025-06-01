from django.urls import path
from .views import *

urlpatterns = [
    path('products', ProductAPIView.as_view()),
    path('create-order/', CreateOrUpdateOrderView.as_view()),
    path('cart-data/', CartDataView.as_view()),
    path('update-cart/', updateCartView.as_view()),
    path('process-order/', ProcessOrderView.as_view()),
    path('unauth-process-order/', UnAuthProcessOrderView.as_view()),
    path('search/', ProductSearchView.as_view()),
    path('products/filter/', FilteredProductListView.as_view()),

]
