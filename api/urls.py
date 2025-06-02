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
    path('relationships/', OrganizationRelationshipListView.as_view(), name='relationship-list'),
    path('relationships/request/', OrganizationRelationshipRequestView.as_view(), name='relationship-request'),
    path('relationships/<int:pk>/update/', OrganizationRelationshipUpdateView.as_view(), name='relationship-update'),
]
