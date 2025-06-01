from django.urls import path
from .views import *
app_name = 'api'
urlpatterns = [
    path('products', ProductAPIView.as_view()),
    path('create-order/', CreateOrUpdateOrderView.as_view()),
    path('cart-data/', CartDataView.as_view()),
    path('update-cart/', updateCartView.as_view()),
    path('process-order/', ProcessOrderView.as_view()),
    path('unauth-process-order/', UnAuthProcessOrderView.as_view()),
    path('search/', ProductSearchView.as_view()),
    path('products/filter/', FilteredProductListView.as_view()),
    path('onboarding/', OrganizationOnboardingView.as_view(), name='organization-onboarding'),
    path('organizations/activate/<uuid:token>/', OrganizationActivationView.as_view(), name='activate-organization'),
    path('buyers/', BuyerCreateView.as_view(), name='buyer-create'),
    path('suppliers/', SupplierCreateView.as_view(), name='supplier-create'),
    path('drivers/', DriverCreateView.as_view(), name='driver-create'),
]
