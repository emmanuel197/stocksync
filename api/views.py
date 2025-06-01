from django.shortcuts import get_object_or_404
from .serializers import ProductSerializer, OrganizationSerializer, BuyerSerializer, SupplierSerializer, DriverSerializer # Import new serializers
from .models import Product, Order, OrderItem, ShippingAddress, ProductImage, ProductSize, Buyer, Brand, Supplier, Driver, Category, Location, Inventory, InventoryMovement # Import new models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny # Import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
from django.db.models import Q
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import EmailMessage, send_mail # Import send_mail
from django.template.loader import render_to_string # Import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Prefetch
from django.urls import reverse # Import reverse
from django.utils.encoding import force_bytes # Import force_bytes
from django.utils.http import urlsafe_base64_encode # Import urlsafe_base64_encode
from accounts.permissions import IsBuyer, IsAdminOrManager, IsStaff # Import custom permissions

from accounts.models import Organization, User # Import Organization and User models

# Create your views here.
class ProductAPIView(generics.ListAPIView):
    queryset = Product.objects.prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all()),
        Prefetch('sizes', queryset=ProductSize.objects.all())
    )
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated] # Accessible to all authenticated users

class FilteredProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    permission_classes = [IsAuthenticated] # Accessible to all authenticated users

class ProductSearchView(APIView):
    permission_classes = [IsAuthenticated] # Accessible to all authenticated users

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q')
        if query:
            products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)
    
def get_item_list(items):
    
    return [
        {
            'id': item.product.id,
            'product': item.product.name,
            'price': item.product.price,
            'image': item.product.image.url,
            'quantity': item.quantity,
            'total': item.get_total,
            'total_completed_orders': item.product.get_completed,
        }
        for item in items
    ]
class CreateOrUpdateOrderView(APIView):
    permission_classes = [IsAuthenticated, IsBuyer] # Accessible to authenticated Buyers
    authentication_classes = [JWTAuthentication]
    def post(self, request, *args, **kwargs):
        data = request.data
        product_id = data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        buyer, created = Buyer.objects.get_or_create(user=request.user, first_name=request.user.first_name, last_name=request.user.last_name, email=request.user.email)
        order, created = Order.objects.get_or_create(customer=buyer, complete=False)
        order_item, created = OrderItem.objects.get_or_create(
            order=order, 
            product=product,
            defaults={'quantity': 1}
        )

        if not created:
            order_item.quantity += 1
            order_item.save()
        
        updated_order_item = OrderItem.objects.select_related('product').get(id=order_item.id)
        item_data = {
            'id': updated_order_item.product.id,
            'product': updated_order_item.product.name,
            'price': updated_order_item.product.price,
            'image': updated_order_item.product.image.url,
            'quantity': updated_order_item.quantity,
            'total': updated_order_item.get_total,
            'total_completed_orders': updated_order_item.product.get_completed,
        }

        return Response({'message': 'Order created successfully', 'total_items': order.get_cart_items,
                'total_cost': order.get_cart_total,
                'updated_item': item_data}, status=status.HTTP_200_OK)

    
class CartDataView(APIView):
    permission_classes = [IsAuthenticated, IsBuyer] # Accessible to authenticated Buyers
    authentication_classes =[JWTAuthentication]

   
    def get(self, request, *args, **kwargs):
        buyer, created = Buyer.objects.get_or_create(user=request.user, first_name=request.user.first_name, last_name=request.user.last_name, email=request.user.email)
        order, order_created = Order.objects.get_or_create(customer=buyer, complete=False)
        items = order.orderitem_set.all()
        
        if len(items) == 0:
            return Response({"QUERY ERROR: No Such Order Item Exists"}, status=status.HTTP_404_NOT_FOUND)
        item_list = get_item_list(items)

        cart_data = {
                'total_items': order.get_cart_items,
                'total_cost': order.get_cart_total,
                'items': item_list,
                'shipping': order.shipping,
                'order_status': order.complete
            }

        return Response(cart_data)

class updateCartView(APIView):
    authentication_classes = [  JWTAuthentication ]
    permission_classes = [ IsAuthenticated, IsBuyer ] # Accessible to authenticated Buyers
    
    def post(self, request, format=None):
        data = request.data
        product_id = data.get('product_id')
        action = data.get('action')
        product = Product.objects.get(id=product_id)
        buyer, created = Buyer.objects.get_or_create(user=request.user, first_name=request.user.first_name, last_name=request.user.last_name, email=request.user.email)
        order, order_created  = Order.objects.get_or_create(customer=buyer, complete=False)
        order_item, order_item_created = OrderItem.objects.get_or_create(order=order, product=product)


        if 'add' == action:

            order_item.quantity += 1
            order_item.save()
        elif 'remove' == action:
            order_item.quantity -= 1
            if order_item.quantity <= 0:
                order_item.delete()
            else:
                order_item.save()
        try:
            updated_order_item = OrderItem.objects.select_related('product').get(id=order_item.id)
            item_data = {
                'id': updated_order_item.product.id,
                'product': updated_order_item.product.name,
                'price': updated_order_item.product.price,
                'image': updated_order_item.product.image.url,
                'quantity': updated_order_item.quantity,
                'total': updated_order_item.get_total,
                'total_completed_orders': updated_order_item.product.get_completed,
            }
            return Response({'message': 'Cart updated successfully', 'total_items': order.get_cart_items,
                'total_cost': order.get_cart_total,
                'updated_item': item_data}, status=status.HTTP_200_OK)
        except OrderItem.DoesNotExist:
            return Response({'item_id': product_id, 'total_items': order.get_cart_items,
                'total_cost': order.get_cart_total, 'error': 'Item does not exist'}, status=status.HTTP_200_OK)
        

def send_purchase_confirmation_email(user_email, first_name, order, total):
    shipping_address = None
    if order.shipping:
        shipping_address = order.shippingaddress_set.all().first()  # Assuming you have a ShippingAddress model associated with the order
     
    template = render_to_string('api/email_template.html', {'order': order,
                                                            'orderitems': order.orderitem_set.all(),
                                                        "first_name": first_name, 
                                                        "total": total,
                                                        'shipping_address': shipping_address
                                                        })
    email = EmailMessage(
        'Your purchase has been confirmed',
        template,
        settings.EMAIL_HOST_USER,
        [user_email],
    )
    email.fail_silently=False
    email.send()

class ProcessOrderView(APIView):
    permission_classes = [ IsAuthenticated, IsAdminOrManager | IsStaff ] # Accessible to authenticated Staff, Managers, or Admins
    authentication_classes = [ JWTAuthentication ]
    def post(self, request, format=None):         
        user_info = request.data.get('user_info')
        shipping_info = request.data.get('shipping_info')
        total = request.data.get('total')
        
        buyer = request.user.buyer
        order, created = Order.objects.get_or_create(customer=buyer, complete=False)

        # Add your order processing logic here

        # For example, you might update the order's status to 'processed'
        
        if total == float(order.get_cart_total):
            order.complete = True
            order.date_completed = timezone.now()
            order.save()
    
        if order.shipping == True:
            ShippingAddress.objects.create(
            customer=buyer,
            order=order,
            address=shipping_info['address'],
            city=shipping_info['city'],
            state=shipping_info['state'],
            zipcode=shipping_info['zipcode'],
            country=shipping_info['country']
            )
        send_purchase_confirmation_email(request.user.email, request.user.first_name, order, total)

        
        return Response({'order_status': order.complete, 'redirect': '/'}, status=status.HTTP_200_OK)

class UnAuthProcessOrderView(APIView):
    def post(self, request, format=None):         
        user_info = request.data.get('user_info')
        shipping_info = request.data.get('shipping_info')
        total = request.data.get('total')
        first_name = user_info['first_name']
        last_name = user_info['last_name']
        email = user_info['email']

        buyer, created = Buyer.objects.get_or_create(first_name=first_name, last_name=last_name, email=email)
        order, created = Order.objects.get_or_create(customer=buyer, complete=False)
        cart = json.loads(request.COOKIES['cart'])
        for i in cart:
            if cart[i]['quantity'] > 0:  
                product = Product.objects.get(id=i)
                OrderItem.objects.get_or_create(
                order=order, 
                product=product,
                defaults={'quantity': cart[i]['quantity']}
            )
        
        if round(total, 2) == float(order.get_cart_total):
            order.complete = True
            order.date_completed = timezone.now()
            order.save()
        
        if order.shipping == True:
            ShippingAddress.objects.create(
            customer=buyer,
            order=order,
            address=shipping_info['address'],
            city=shipping_info['city'],
            state=shipping_info['state'],
            zipcode=shipping_info['zipcode'],
            country=shipping_info['country']
            )
        send_purchase_confirmation_email(email, first_name, order, total)
        
        return Response({'order_status': order.complete, 'redirect': '/'}, status=status.HTTP_200_OK)

def send_organization_activation_email(organization):
    """Sends an activation email to the organization's contact email."""
    subject = 'Activate Your StockSync Organization'
    # Construct the activation link
    activation_link = settings.FRONTEND_URL + reverse('api:activate-organization', kwargs={'token': organization.activation_token})

    template = render_to_string('api/organization_activation_email.html', {
        'organization_name': organization.name,
        'activation_link': activation_link,
    })

    email = EmailMessage(
        subject,
        template, # Use the rendered template directly as the body
        settings.EMAIL_HOST_USER, # Use EMAIL_HOST_USER as the sender to match the format
        [organization.contact_email],
    )
    email.fail_silently = False

    try:
        email.send()
        organization.email_sent = True
        organization.save(update_fields=['email_sent'])
        print(f"Activation email sent successfully to {organization.contact_email}") # Debug print
    except Exception as e:
        print(f"Error sending activation email to {organization.contact_email}: {e}")
        # Optionally handle the error, e.g., log it or mark the organization for manual activation

class OrganizationCreateView(generics.CreateAPIView):
    """API endpoint for creating a new Organization."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [AllowAny] # Or restrict as needed for your onboarding flow

    def perform_create(self, serializer):
        # Save the organization with active_status=False by default
        organization = serializer.save(active_status=False)
        # Send activation email
        if organization.contact_email:
            try:
                send_organization_activation_email(organization)
            except Exception as e:
                print(f"Error sending activation email to {organization.contact_email}: {e}")
                # Optionally handle the error, e.g., log it or mark the organization for manual activation

class OrganizationActivationView(APIView):
    """API endpoint for activating an Organization via email link."""
    permission_classes = [AllowAny]

    def get(self, request, token, *args, **kwargs):
        try:
            organization = Organization.objects.get(activation_token=token)
        except Organization.DoesNotExist:
            return Response({'detail': 'Invalid activation token.'}, status=status.HTTP_400_BAD_REQUEST)

        if organization.active_status:
            return Response({'detail': 'Organization already active.'}, status=status.HTTP_200_OK)

        organization.active_status = True
        organization.save(update_fields=['active_status'])

        return Response({'detail': 'Organization activated successfully.'}, status=status.HTTP_200_OK)

class BuyerCreateView(generics.CreateAPIView):
    """API endpoint for creating a new Buyer entity within an organization."""
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager] # Restricted to authenticated Admins/Managers

    def perform_create(self, serializer):
        # Automatically associate the buyer with the user's organization
        serializer.save(organization=self.request.user.organization)

class SupplierCreateView(generics.CreateAPIView):
    """API endpoint for creating a new Supplier entity within an organization."""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager] # Restricted to authenticated Admins/Managers

    def perform_create(self, serializer):
        # Automatically associate the supplier with the user's organization
        serializer.save(organization=self.request.user.organization)

class DriverCreateView(generics.CreateAPIView):
    """API endpoint for creating a new Driver entity within an organization."""
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager] # Restricted to authenticated Admins/Managers

    def perform_create(self, serializer):
        # Automatically associate the driver with the user's organization
        serializer.save(organization=self.request.user.organization)
