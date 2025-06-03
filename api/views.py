from django.shortcuts import get_object_or_404
from .serializers import (
    ProductSerializer, OrganizationSerializer, BuyerSerializer, SupplierSerializer, DriverSerializer, 
    OrganizationOnboardingSerializer, OrganizationRelationshipSerializer, PotentialSupplierSerializer,
    InventorySerializer, InventoryMovementSerializer, ProductCreateSerializer, InventoryCreateSerializer,
    BrandSerializer, CategorySerializer, LocationSerializer
)
from .models import (
    Product, Order, OrderItem, ShippingAddress, ProductImage, ProductSize, Buyer, Brand, Supplier, Driver, 
    Category, Location, Inventory, InventoryMovement
)
from accounts.models import Organization, OrganizationRelationship, User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
from django.db.models import Q, Prefetch, Sum
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from accounts.permissions import IsBuyer, IsAdminOrManager, IsStaff
from djoser.conf import settings as djoser_settings
from django.db import transaction

# Create your views here.
class ProductAPIView(generics.ListAPIView):
    """
    Lists products based on the authenticated user's organization type and relationships.
    Suppliers see their own products.
    Buyers see products from accepted supplier relationships.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated] # Require authentication

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            # User is authenticated but not associated with an organization
            return Product.objects.none()

        if organization.organization_type in ['supplier', 'both', 'internal']:
            # Supplier or internal users see their own products
            return Product.objects.filter(organization=organization).order_by('name')

        elif organization.organization_type == 'buyer':
            # Buyers see products from suppliers they have an accepted relationship with
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)

            return Product.objects.filter(organization__id__in=accepted_supplier_ids).order_by('name')

        # Default case or other organization types not explicitly handled
        return Product.objects.none()

class FilteredProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    permission_classes = [IsAuthenticated]

class ProductSearchView(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated, IsBuyer]
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
    permission_classes = [IsAuthenticated, IsBuyer]
    authentication_classes = [JWTAuthentication]

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsBuyer]
    
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
        shipping_address = order.shippingaddress_set.all().first()
     
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
    permission_classes = [IsAuthenticated, IsAdminOrManager | IsStaff]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):         
        user_info = request.data.get('user_info')
        shipping_info = request.data.get('shipping_info')
        total = request.data.get('total')
        
        buyer = request.user.buyer
        order, created = Order.objects.get_or_create(customer=buyer, complete=False)

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
    subject = 'Activate Your StockSync Organization'
    activation_link = settings.FRONTEND_URL + reverse('api:activate-organization', kwargs={'token': organization.activation_token})

    template = render_to_string('api/organization_activation_email.html', {
        'organization_name': organization.name,
        'activation_link': activation_link,
    })

    email = EmailMessage(
        subject,
        template,
        settings.EMAIL_HOST_USER,
        [organization.contact_email],
    )
    email.fail_silently = False

    try:
        email.send()
        organization.email_sent = True
        organization.save(update_fields=['email_sent'])
        print(f"Activation email sent successfully to {organization.contact_email}")
    except Exception as e:
        print(f"Error sending activation email to {organization.contact_email}: {e}")

class OrganizationCreateView(generics.CreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        organization = serializer.save(active_status=False)
        if organization.contact_email:
            try:
                send_organization_activation_email(organization)
            except Exception as e:
                print(f"Error sending activation email to {organization.contact_email}: {e}")

class OrganizationActivationView(APIView):
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

class OrganizationOnboardingView(generics.CreateAPIView):
    serializer_class = OrganizationOnboardingSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        created_objects = serializer.save()
        organization = created_objects['organization']
        user = created_objects['user']

        if djoser_settings.SEND_ACTIVATION_EMAIL:
             try:
                 djoser_settings.EMAIL.activation(self.request, {"user": user}).send([user.email])
                 print(f"Djoser activation email triggered for user: {user.email}")
             except Exception as e:
                 print(f"Error triggering Djoser activation email for user {user.email}: {e}")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"detail": "Organization and initial user created. Please check the user's email for activation."},
            status=status.HTTP_201_CREATED
        )

class OrganizationRelationshipListView(generics.ListAPIView):
    serializer_class = OrganizationRelationshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return OrganizationRelationship.objects.none()

        queryset = OrganizationRelationship.objects.filter(
            Q(buyer_organization=organization) | Q(supplier_organization=organization)
        )

        status = self.request.query_params.get('status')
        if status in ['pending', 'accepted', 'rejected']:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

class OrganizationRelationshipRequestView(generics.CreateAPIView):
    serializer_class = OrganizationRelationshipSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class OrganizationRelationshipUpdateView(generics.UpdateAPIView):
    queryset = OrganizationRelationship.objects.all()
    serializer_class = OrganizationRelationshipSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return OrganizationRelationship.objects.none()

        queryset = OrganizationRelationship.objects.filter(
            Q(buyer_organization=organization) | Q(supplier_organization=organization),
            status='pending'
        ).exclude(initiated_by__organization=organization)

        return queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get('status')
        if new_status not in ['accepted', 'rejected']:
             raise serializers.ValidationError({"status": "Status can only be changed to 'accepted' or 'rejected'."})

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

class PotentialSupplierListView(generics.ListAPIView):
    """
    API endpoint to list organizations that can act as suppliers.
    Accessible to authenticated users from buyer or 'both' organizations.
    """
    serializer_class = PotentialSupplierSerializer
    permission_classes = [IsAuthenticated] # Only authenticated users can see this list

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Organization.objects.none() # User not associated with an organization

        # Only allow users from buyer or 'both' organizations to see potential suppliers
        if organization.organization_type not in ['buyer', 'both']:
            return Organization.objects.none()

        # Filter organizations that are suppliers or 'both'
        queryset = Organization.objects.filter(organization_type__in=['supplier', 'both'])

        # Exclude the user's own organization from the list
        queryset = queryset.exclude(id=organization.id)

        return queryset.order_by('name')

class InventoryListView(generics.ListAPIView):
    """
    List inventory items available to the authenticated user's organization
    based on accepted supplier relationships (for buyers) or their own inventory (for suppliers).
    """
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Inventory.objects.none()

        # Prefetch related product and location for efficiency
        queryset = Inventory.objects.select_related('product', 'location')

        # If the user's organization is a Buyer (or both), they should see inventory
        # from products belonging to organizations they have an 'accepted' supplier relationship with.
        if organization.organization_type in ['buyer', 'both']:
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)

            # Filter inventory where the related product's organization is in the accepted supplier IDs
            queryset = queryset.filter(product__organization__id__in=accepted_supplier_ids)

        # If the user's organization is a Supplier (or both), they should see their own inventory.
        elif organization.organization_type in ['supplier', 'internal']:
             # Filter inventory where the related product's organization is the current organization
             queryset = queryset.filter(product__organization=organization)

        else:
            # Other organization types might have different access rules
            queryset = Inventory.objects.none()

        return queryset.order_by('product__name', 'location__name')


class InventoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific inventory item, ensuring the user's organization
    has access based on relationships.
    """
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Inventory.objects.none()

        # Prefetch related product and location
        queryset = Inventory.objects.select_related('product', 'location')

        if organization.organization_type in ['buyer', 'both']:
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)
            queryset = queryset.filter(product__organization__id__in=accepted_supplier_ids)

        elif organization.organization_type in ['supplier', 'internal']:
             queryset = queryset.filter(product__organization=organization)

        else:
            queryset = Inventory.objects.none()

        return queryset


class InventoryCreateView(generics.CreateAPIView):
    """
    Allows users from supplier or 'both' organizations to create new inventory items.
    Creates an InventoryMovement record for the initial stock.
    """
    queryset = Inventory.objects.all()
    serializer_class = InventoryCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager] # Or a custom permission for inventory managers

    def perform_create(self, serializer):
        user = self.request.user
        organization = user.organization

        if organization and organization.organization_type in ['supplier', 'both', 'internal']:
            # Get the initial quantity before saving
            initial_quantity = serializer.validated_data.get('quantity', 0)

            # Save the inventory instance
            inventory_instance = serializer.save(organization=organization)

            # Create an InventoryMovement record for the initial stock
            if initial_quantity > 0:
                InventoryMovement.objects.create(
                    inventory=inventory_instance,
                    movement_type='addition', # Or 'initial_stock'
                    quantity_change=initial_quantity,
                    user=user,
                    organization=organization
                )

        else:
            raise serializers.ValidationError("Your organization type is not authorized to create inventory.")

class InventoryUpdateView(generics.RetrieveUpdateAPIView):
    """
    Allows users from supplier or 'both' organizations to update inventory quantity.
    Ensures the inventory item belongs to the user's organization.
    Creates an InventoryMovement record for the change.
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Inventory.objects.none()

        if organization.organization_type in ['supplier', 'both', 'internal']:
             queryset = Inventory.objects.filter(product__organization=organization)
             return queryset
        else:
            return Inventory.objects.none()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_quantity = instance.quantity # Get quantity before update

        response = super().update(request, *args, **kwargs) # Perform the update

        instance.refresh_from_db() # Refresh instance to get the new quantity
        new_quantity = instance.quantity

        quantity_change = new_quantity - old_quantity

        if quantity_change != 0:
            movement_type = 'adjustment'
            if quantity_change > 0:
                movement_type = 'addition'
            elif quantity_change < 0:
                movement_type = 'subtraction'

            user = self.request.user
            organization = user.organization

            InventoryMovement.objects.create(
                inventory=instance,
                movement_type=movement_type,
                quantity_change=quantity_change,
                user=user,
                organization=organization
            )

        return response


class InventoryMovementListView(generics.ListAPIView):
    """
    Lists inventory movements for the user's organization,
    filtered based on their organization type and relationships.
    """
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return InventoryMovement.objects.none()

        # Start with all movements for the user's organization
        queryset = InventoryMovement.objects.filter(organization=organization)

        # Prefetch related inventory, product, and user for efficiency
        # Use select_related for ForeignKey relationships
        queryset = queryset.select_related('inventory__product', 'user')

        # Filter movements based on the accessibility of the related inventory item
        if organization.organization_type in ['buyer', 'both']:
            # Buyers see movements for inventory items belonging to products
            # from organizations they have an 'accepted' supplier relationship with.
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)

            queryset = queryset.filter(inventory__product__organization__id__in=accepted_supplier_ids)

        elif organization.organization_type in ['supplier', 'internal']:
             # Suppliers/Internal users see movements for inventory items
             # belonging to products from their own organization.
             queryset = queryset.filter(inventory__product__organization=organization)

        else:
            # Other organization types might have different access rules
            queryset = InventoryMovement.objects.none()


        return queryset.order_by('-timestamp')

class ProductCreateView(generics.CreateAPIView):
    """
    Allows users from supplier or 'both' organizations to create new products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def perform_create(self, serializer):
        user = self.request.user
        organization = user.organization
        if organization and organization.organization_type in ['supplier', 'both', 'internal']:
            serializer.save(organization=organization)
        else:
            raise serializers.ValidationError("Your organization type is not authorized to create products.")

class BrandListView(generics.ListCreateAPIView):
    """
    Lists and allows creation of Brands for the authenticated user's organization.
    """
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Brand.objects.none()

        # Only list brands belonging to the user's organization
        return Brand.objects.filter(organization=organization).order_by('name')

    def perform_create(self, serializer):
        # Associate the brand with the authenticated user's organization
        user = self.request.user
        organization = user.organization
        if organization and organization.organization_type in ['supplier', 'both', 'internal']:
            serializer.save(organization=organization)
        else:
            raise serializers.ValidationError("Your organization type is not authorized to create brands.")

class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a specific Brand belonging to the
    authenticated user's organization.
    """
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Brand.objects.none()

        # Only allow access to brands belonging to the user's organization
        return Brand.objects.filter(organization=organization)

class CategoryListView(generics.ListCreateAPIView):
    """
    Lists and allows creation of Categories for the authenticated user's organization.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Category.objects.none()

        # Only list categories belonging to the user's organization
        return Category.objects.filter(organization=organization).order_by('name')

    def perform_create(self, serializer):
        # Associate the category with the authenticated user's organization
        user = self.request.user
        organization = user.organization
        if organization and organization.organization_type in ['supplier', 'both', 'internal']:
            serializer.save(organization=organization)
        else:
            raise serializers.ValidationError("Your organization type is not authorized to create categories.")

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a specific Category belonging to the
    authenticated user's organization.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Category.objects.none()

        # Only allow access to categories belonging to the user's organization
        return Category.objects.filter(organization=organization)

class LocationListView(generics.ListCreateAPIView):
    """
    Lists and allows creation of Locations for the authenticated user's organization.
    """
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager] # Or a custom permission for location managers

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Location.objects.none()

        # Only list locations belonging to the user's organization
        return Location.objects.filter(organization=organization).order_by('name')

    def perform_create(self, serializer):
        # Associate the location with the authenticated user's organization
        user = self.request.user
        organization = user.organization
        if organization and organization.organization_type in ['supplier', 'both', 'internal']:
            serializer.save(organization=organization)
        else:
            raise serializers.ValidationError("Your organization type is not authorized to create locations.")

class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a specific Location belonging to the
    authenticated user's organization.
    """
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager] # Or a custom permission for location managers
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Location.objects.none()

        # Only allow access to locations belonging to the user's organization
        return Location.objects.filter(organization=organization)