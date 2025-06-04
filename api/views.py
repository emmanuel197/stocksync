from django.shortcuts import get_object_or_404
from .serializers import (
    ProductSerializer, OrganizationSerializer, BuyerSerializer, SupplierSerializer, DriverSerializer, 
    OrganizationOnboardingSerializer, OrganizationRelationshipSerializer, PotentialSupplierSerializer,
    InventorySerializer, InventoryMovementSerializer, ProductCreateSerializer, InventoryCreateSerializer,
    BrandSerializer, CategorySerializer, LocationSerializer, BuyerSupplierInventorySerializer,
    BuyerSupplierProductSerializer, OrderSerializer # Ensure BuyerSupplierProductSerializer and OrderSerializer are imported
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
from decimal import Decimal

# Create your views here.
class ProductAPIView(generics.ListAPIView):
    """
    Lists products based on the authenticated user's organization type and relationships.
    Suppliers see their own products.
    Buyers see products from accepted supplier relationships.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated] # Require authentication

    def get_serializer_class(self):
        user = self.request.user
        organization = user.organization

        if organization and organization.organization_type in ['buyer', 'both']:
            print("Using BuyerSupplierProductSerializer") # Add this line
            return BuyerSupplierProductSerializer
        else:
            print("Using ProductSerializer") # Add this line
            return ProductSerializer

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
    """
    Lists filtered products based on the authenticated user's organization type and relationships.
    Suppliers see their own products with cost.
    Buyers see products from accepted supplier relationships without cost.
    """
    queryset = Product.objects.all() # Queryset is filtered in get_queryset
    # serializer_class is now determined dynamically
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        organization = user.organization

        if organization and organization.organization_type in ['buyer', 'both']:
            return BuyerSupplierProductSerializer
        else:
            return ProductSerializer

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Product.objects.none()

        # Start with the base queryset
        queryset = Product.objects.all()

        # Apply organization-based filtering similar to ProductAPIView
        if organization.organization_type in ['supplier', 'both', 'internal']:
            queryset = queryset.filter(organization=organization)
        elif organization.organization_type == 'buyer':
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)
            queryset = queryset.filter(organization__id__in=accepted_supplier_ids)
        else:
            return Product.objects.none() # Other organization types not explicitly handled

        # DjangoFilterBackend will apply filters on top of this queryset
        return queryset.order_by('name')

class ProductSearchView(APIView):
    """
    Searches products based on the authenticated user's organization type and relationships.
    Suppliers search their own products.
    Buyers search products from accepted supplier relationships.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q')
        user = self.request.user
        organization = user.organization

        if not organization:
            return Response([], status=status.HTTP_200_OK)

        # Filter products based on organization type and relationships
        if organization.organization_type in ['supplier', 'both', 'internal']:
            queryset = Product.objects.filter(organization=organization)
        elif organization.organization_type == 'buyer':
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)
            queryset = Product.objects.filter(organization__id__in=accepted_supplier_ids)
        else:
            return Response([], status=status.HTTP_200_OK) # Other organization types

        # Apply search query
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        # Select serializer based on user type
        if organization.organization_type in ['buyer', 'both']:
            serializer = BuyerSupplierProductSerializer(queryset, many=True, context={'request': request})
        else:
            serializer = ProductSerializer(queryset, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)

def get_item_list(items):
    return [
        {
            'id': item.product.id,
            'product': item.product.name,
            'price': item.product.price,
            'image': item.product.image.url if item.product.image else None, # Handle potential missing image
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

        user = request.user
        if not hasattr(user, 'organization') or not user.organization:
             return Response({"detail": "User is not associated with an organization."}, status=status.HTTP_400_BAD_REQUEST)

        buyer, created = Buyer.objects.get_or_create(
            user=user,
            defaults={
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'organization': user.organization
            }
        )

        if not buyer.organization:
             if hasattr(user, 'organization') and user.organization:
                 buyer.organization = user.organization
                 buyer.save()
             else:
                 return Response({"detail": "Buyer is not associated with an organization."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create the pending order for this buyer
        order, created = Order.objects.get_or_create(
            customer=buyer,
            status='pending',
        )

        # Explicitly set the organization on the order if it's not already set
        # This handles cases where an existing order without an organization is retrieved
        if not order.organization:
            order.organization = buyer.organization
            order.save() # Save the order if the organization was just set

        # Ensure the order has an organization before creating OrderItem
        if not order.organization:
             return Response({"detail": "Could not determine organization for the order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get or create the order item
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={
                'quantity': 1,
                'unit_price': product.price,
                'organization': order.organization
            }
        )

        if not created:
            order_item.quantity += 1
            order_item.save()

        return Response({"message": "Item added/updated in cart"}, status=status.HTTP_200_OK)

class CartDataView(APIView):
    permission_classes = [IsAuthenticated, IsBuyer]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        print("--- Inside CartDataView GET method ---")
        user = request.user
        print(f"User: {user}")
        print(f"User authenticated: {user.is_authenticated}")
        print(f"User organization: {user.organization if hasattr(user, 'organization') else 'None'}")

        if not hasattr(user, 'organization') or not user.organization:
             print("User not associated with an organization.")
             return Response({"detail": "User is not associated with an organization."}, status=status.HTTP_400_BAD_REQUEST)

        # Assuming a Buyer profile exists for the user (created during login or first cart interaction)
        try:
            buyer = Buyer.objects.get(user=user)
            print(f"Found Buyer profile for user: {buyer.id}")
        except Buyer.DoesNotExist:
            print("No Buyer profile found for the user. Cart is empty.")
            # If no Buyer profile exists, the cart is empty
            return Response({"items": [], "total_amount": "0.00"}, status=status.HTTP_200_OK)

        # Find the pending order for this buyer
        # Change complete=False to status='pending'
        order = Order.objects.filter(customer=buyer, status='pending').first()

        if order:
            print(f"Found pending order: {order.id}")
            # Serialize the order data, including its items
            # Pass the request context to the serializer
            serializer = OrderSerializer(order, context={'request': request}) # Added context={'request': request}
            print("OrderSerializer initialized with request context.")
            print("--- Exiting CartDataView GET method (Success) ---")
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print("No pending order found for the buyer. Cart is empty.")
            # If no pending order exists, the cart is empty
            print("--- Exiting CartDataView GET method (No Order) ---")
            return Response({"items": [], "total_amount": "0.00"}, status=status.HTTP_200_OK)

class updateCartView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsBuyer]

    # Changed from post to patch
    def patch(self, request, format=None):
        print("--- Inside updateCartView PATCH method ---") # Updated print statement
        data = request.data
        product_id = data.get('product_id')
        action = data.get('action')
        amount = data.get('amount')
        print(f"Received data: product_id={product_id}, action={action}, amount={amount}")

        # Validate action
        if action not in ['add', 'remove']:
            print(f"Invalid action received: {action}")
            return Response({"detail": "Invalid action. Must be 'add' or 'remove'."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate amount is a positive integer
        try:
            amount = int(amount)
            if amount <= 0:
                print(f"Invalid amount received: {amount}")
                return Response({"detail": "Amount must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
            print(f"Amount validated: {amount}")
        except (ValueError, TypeError):
            print(f"Invalid amount format received: {amount}")
            return Response({"detail": "Invalid amount provided."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)
        user = request.user
        print(f"User: {user}, Product: {product.name}")

        if not hasattr(user, 'organization') or not user.organization:
             print("updateCartView: User not associated with an organization.")
             return Response({"detail": "User is not associated with an organization."}, status=status.HTTP_400_BAD_REQUEST)

        buyer, created = Buyer.objects.get_or_create(
            user=user,
            defaults={
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'organization': user.organization # Ensure buyer is linked to organization
            }
        )
        print(f"updateCartView: Retrieved/Created Buyer: {buyer} (ID: {buyer.id}), Created: {created}")

        if not buyer.organization:
             if hasattr(user, 'organization') and user.organization:
                 buyer.organization = user.organization
                 buyer.save()
                 print(f"updateCartView: Buyer organization set to: {buyer.organization}")
             else:
                 print("updateCartView: Buyer is not associated with an organization after get_or_create.")
                 return Response({"detail": "Buyer is not associated with an organization."}, status=status.HTTP_400_BAD_REQUEST)


        # Get or create the pending order for this buyer
        order, order_created  = Order.objects.get_or_create(customer=buyer, status='pending')
        print(f"updateCartView: Retrieved/Created Order: {order} (ID: {order.id}), Created: {order_created}")

        # Explicitly set the organization on the order if it's not already set
        if not order.organization:
            order.organization = buyer.organization
            order.save()
            print(f"updateCartView: Order organization set to: {order.organization}")

        # Ensure the order has an organization before proceeding
        if not order.organization:
             print("updateCartView: Could not determine organization for the order.")
             return Response({"detail": "Could not determine organization for the order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # Use a transaction for atomicity
        with transaction.atomic():
            print("updateCartView: Starting atomic transaction.")
            # Get or create the order item
            order_item, order_item_created = OrderItem.objects.get_or_create(
                order=order,
                product=product,
                defaults={
                    'quantity': 0, # Start with 0 if creating
                    'unit_price': product.price,
                    'organization': order.organization # Link order item to order's organization
                }
            )
            print(f"updateCartView: OrderItem: {order_item}, Created: {order_item_created}")

            current_quantity = order_item.quantity
            new_quantity = current_quantity
            print(f"updateCartView: Current quantity: {current_quantity}")

            if action == 'add':
                new_quantity = current_quantity + amount
                message = 'Item quantity increased'
                print(f"updateCartView: Action 'add'. New quantity calculated: {new_quantity}")
            elif action == 'remove':
                new_quantity = current_quantity - amount
                message = 'Item quantity decreased'
                print(f"updateCartView: Action 'remove'. New quantity calculated: {new_quantity}")

            # Ensure new quantity is not negative
            new_quantity = max(0, new_quantity)
            print(f"updateCartView: Final new quantity (min 0): {new_quantity}")

            if new_quantity <= 0:
                # If the new quantity is 0 or less, delete the item
                if not order_item_created: # Only delete if the item already existed
                    order_item_id_to_delete = order_item.id # Store ID before deletion
                    order_item.delete()
                    updated_item_data = None # Item was deleted
                    message = 'Item removed from cart'
                    print(f"updateCartView: New quantity <= 0. Deleted OrderItem ID: {order_item_id_to_delete}")
                else:
                    # Item was just created with quantity 0, no need to delete
                    updated_item_data = None
                    message = 'Item quantity is zero'
                    print("updateCartView: OrderItem was just created with quantity 0. No deletion needed.")

            else:
                # If the new quantity is greater than 0, update the quantity
                order_item.quantity = new_quantity
                order_item.unit_price = product.price # Ensure unit price is current
                order_item.save()
                print(f"updateCartView: OrderItem quantity updated to {order_item.quantity} and saved.")
                # message is already set based on action

                # Prepare updated item data for the response
                # Re-fetch the order item to get updated calculated properties like get_total
                try:
                    # Use select_related to avoid extra query for product
                    updated_order_item = OrderItem.objects.select_related('product').get(id=order_item.id)
                    updated_item_data = {
                        'id': updated_order_item.product.id,
                        'product': updated_order_item.product.name,
                        'price': str(updated_order_item.product.price), # Ensure decimal is string
                        'image': updated_order_item.product.image.url if updated_order_item.product.image else None,
                        'quantity': updated_order_item.quantity,
                        'total': str(updated_order_item.get_total), # Use the property
                        'total_completed_orders': updated_order_item.product.get_completed,
                    }
                    print(f"updateCartView: Updated item data prepared: {updated_item_data}")
                except OrderItem.DoesNotExist:
                    # This case should ideally not happen if quantity > 0 and save was successful
                    updated_item_data = None
                    print("updateCartView: Error: OrderItem not found after saving.")


            # Re-fetch the order to get updated totals after item changes
            order.refresh_from_db()
            print(f"updateCartView: Order refreshed from DB. Current total items: {order.get_cart_items}, Current total cost: {order.get_cart_total}")
            print(f"updateCartView: Order status after updateCartView transaction: {order.status}") # Added print statement

            print("updateCartView: Transaction successful. Returning response from updateCartView.")
            return Response({
                'message': message,
                'total_items': order.get_cart_items,
                'total_cost': str(order.get_cart_total), # Ensure decimal is string
                'updated_item': updated_item_data # Will be None if item was deleted
            }, status=status.HTTP_200_OK)

def send_purchase_confirmation_email(user_email, first_name, order, total):
    print("--- Inside send_purchase_confirmation_email ---")
    shipping_address = None
    if order.shipping_address:
        shipping_address = order.shippingaddress_set.all().first()
        print(f"Shipping address found: {shipping_address}")

    try:
        template = render_to_string('api/email_template.html', {
            'order': order,
            'orderitems': order.items.all(),
            "first_name": first_name,
            "total": total,
            'shipping_address': shipping_address
        })
        print("Email template rendered successfully.")
    except Exception as e:
        print(f"Error rendering email template: {e}")

    email = EmailMessage(
        'Your purchase has been confirmed',
        template,
        settings.EMAIL_HOST_USER,
        [user_email],
    )
    email.fail_silently=False
    try:
        email.send()
        print(f"Purchase confirmation email sent to {user_email}.")
    except Exception as e:
        print(f"Error sending email to {user_email}: {e}")

class ProcessOrderView(APIView):
    # Allow IsBuyer OR IsAdminOrManager | IsStaff to process orders
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager | IsStaff]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        print("--- Inside ProcessOrderView POST method ---")
        user_info = request.data.get('user_info')
        shipping_info = request.data.get('shipping_info')
        total_str = request.data.get('total') # Get total as string initially
        print(f"Received total string from frontend: {total_str}")

        user = request.user
        organization = user.organization
        print(f"Processing order for User: {user}, Organization: {organization}")

        if not organization:
             print("User not associated with an organization.")
             return Response({"detail": "User is not associated with an organization."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the user is authorized to process orders for this organization type
        if organization.organization_type not in ['buyer', 'supplier', 'both', 'internal']:
             print(f"Organization type {organization.organization_type} not authorized to process orders.")
             return Response({"detail": "Your organization type is not authorized to process orders."}, status=status.HTTP_403_FORBIDDEN)

        # If the user is a buyer, they process their own orders
        if organization.organization_type == 'buyer':
             buyer, created = Buyer.objects.get_or_create(user=user, defaults={'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email})
             print(f"Retrieved/Created Buyer: {buyer} (ID: {buyer.id}), Created: {created}")

             # Get all pending orders for this buyer
             pending_orders = Order.objects.filter(customer=buyer, status='pending').order_by('-order_date')
             print(f"Found {pending_orders.count()} pending orders for buyer {buyer.id}.")
             for po in pending_orders:
                 print(f"- Pending Order ID: {po.id}, Status: {po.status}, Items Count: {po.items.count()}, Total: {po.get_cart_total}")

             # Get the most recent pending order
             order = pending_orders.first()
             print(f"Selected Pending Order: {order} (ID: {order.id if order else 'None'})")


             if not order:
                 print("No pending order found for this buyer.")
                 return Response({"detail": "No pending order found."}, status=status.HTTP_400_BAD_REQUEST)

             # Optional: Check for multiple pending orders (indicates a potential issue in cart logic)
             if pending_orders.count() > 1:
                 print(f"Warning: Multiple pending orders found for buyer {buyer.id}. Processing the most recent one (ID: {order.id}).")
                 # You might want to add more robust handling here, e.g., error or process the most recent one.
                 # For now, we proceed with the most recent one retrieved above.


        # If the user is a supplier/internal/both, they might be processing an order placed by a buyer
        # This part of the logic would need to be more complex to identify which order is being processed.
        # For simplicity in this example, we'll assume the request includes the order ID if not a buyer.
        # However, the prompt focuses on the buyer's perspective completing *their* purchase.
        # So, we'll primarily focus on the buyer completing their own order.
        elif organization.organization_type in ['supplier', 'both', 'internal']:
             # This view is primarily for the buyer completing their own order.
             # Processing orders initiated by buyers from the supplier side would require a different view/logic.
             print("Supplier/Internal user attempting to use buyer process order endpoint.")
             return Response({"detail": "This endpoint is primarily for buyers to complete their own orders."}, status=status.HTTP_403_FORBIDDEN)

        # Get a default location for the buyer's organization
        # You might need more sophisticated logic to determine the correct receiving location
        buyer_default_location = Location.objects.filter(organization=organization).first()
        print(f"Buyer default location: {buyer_default_location}")

        if not buyer_default_location:
             print("Buyer organization has no locations defined.")
             # Handle the case where the buyer's organization has no locations
             return Response({"detail": "Your organization does not have any locations defined. Cannot process order."}, status=status.HTTP_400_BAD_REQUEST)

        # Convert the received total to Decimal for precise comparison
        try:
            received_total = Decimal(total_str)
            print(f"Received total as Decimal: {received_total}")
        except (ValueError, TypeError):
            print(f"Invalid total amount provided: {total_str}")
            return Response({"detail": "Invalid total amount provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Use a transaction to ensure atomicity of inventory updates
        with transaction.atomic():
            print("Starting atomic transaction for order processing.")
            # Check the order items and calculated total before comparison
            order.refresh_from_db() # Ensure the order object is fresh
            print(f"Order {order.id} status: {order.status}")
            print(f"Order {order.id} items count: {order.items.count()}")
            print(f"Order {order.id} calculated total: {order.get_cart_total}")

            # Compare Decimal values
            if received_total == order.get_cart_total: # Compare Decimal with Decimal
                print("Total match. Processing order.")
                order.status = 'completed'
                order.date_completed = timezone.now()
                order.save()
                print(f"Order {order.id} status updated to 'completed'.")

                # Process each order item for inventory updates
                for order_item in order.items.all(): # Use order.items.all() to access related items
                    product = order_item.product
                    quantity_purchased = order_item.quantity
                    print(f"Processing item for inventory update: Product {product.sku}, Quantity {quantity_purchased}")

                    # --- Supplier Inventory Update ---
                    # Find the supplier's inventory item for this product.
                    # This assumes the product belongs to a supplier organization.
                    supplier_organization = product.organization
                    if supplier_organization and supplier_organization.organization_type in ['supplier', 'both']:
                        print(f"Product belongs to supplier organization: {supplier_organization.name}")
                        # Find an inventory item for this product at the supplier's organization.
                        # This might need refinement based on how suppliers manage locations.
                        # For simplicity, we'll try to find any inventory item for the product at the supplier's org.
                        supplier_inventory_item = Inventory.objects.filter(
                            product=product,
                            organization=supplier_organization
                        ).first() # Get the first one found
                        print(f"Supplier inventory item found: {supplier_inventory_item}")

                        if supplier_inventory_item:
                            # Decrease supplier's inventory
                            supplier_inventory_item.quantity -= quantity_purchased
                            supplier_inventory_item.last_sold = timezone.now()
                            supplier_inventory_item.save()
                            print(f"Supplier inventory updated for {product.sku}. New quantity: {supplier_inventory_item.quantity}")

                            # Create supplier inventory movement (subtraction/sale)
                            InventoryMovement.objects.create(
                                inventory=supplier_inventory_item,
                                movement_type='sale',
                                quantity_change=-quantity_purchased, # Negative for subtraction
                                user=user, # User who processed the order (the buyer in this flow)
                                organization=supplier_organization, # The supplier's organization
                                note=f"Sale to {organization.name} (Order {order.id})"
                            )
                            print("Supplier inventory movement recorded.")
                        else:
                            # Handle case where supplier inventory item is not found (e.g., log a warning)
                            print(f"Warning: Supplier inventory item not found for product {product.sku} at organization {supplier_organization.name}")


                    # --- Buyer Inventory Update ---
                    # Find or create the buyer's inventory item for this product.
                    # Use the buyer's default location
                    buyer_inventory_item, created = Inventory.objects.get_or_create(
                        product=product,
                        organization=organization, # The buyer's organization
                        location=buyer_default_location, # Use the fetched location
                        defaults={'quantity': 0} # Start with 0 if creating
                    )
                    print(f"Buyer inventory item found/created: {buyer_inventory_item}, Created: {created}")

                    # Increase buyer's inventory
                    buyer_inventory_item.quantity += quantity_purchased
                    # You might want to set a 'last_received' field here
                    buyer_inventory_item.save()
                    print(f"Buyer inventory updated for {product.sku}. New quantity: {buyer_inventory_item.quantity}")

                    # Create buyer inventory movement (addition/purchase)
                    InventoryMovement.objects.create(
                        inventory=buyer_inventory_item,
                        movement_type='purchase',
                        quantity_change=quantity_purchased, # Positive for addition
                        user=user, # User who processed the order (the buyer)
                        organization=organization, # The buyer's organization
                        note=f"Purchase from {supplier_organization.name} (Order {order.id})"
                    )
                    print("Buyer inventory movement recorded.")

            else:
                # Handle total mismatch (potential fraud or calculation error)
                # Log the mismatch for debugging
                print(f"Total mismatch for Order {order.id}: Received {received_total}, Calculated {order.get_cart_total}")
                return Response({"detail": "Total mismatch. Order not processed."}, status=status.HTTP_400_BAD_REQUEST)


        # Check if shipping is required based on the order object
        if order.shipping_address: # Assuming shipping_address field indicates if shipping is needed
            print("Shipping address exists on order. Creating ShippingAddress object.")
            ShippingAddress.objects.create(
            customer=buyer,
            order=order,
            address=shipping_info.get('address'), # Use .get() for safety
            city=shipping_info.get('city'),
            state=shipping_info.get('state'),
            zipcode=shipping_info.get('zipcode'),
            country=shipping_info.get('country')
            )
            print("ShippingAddress object created.")

        # Pass the Decimal total to the email function
        print("Sending purchase confirmation email.")
        send_purchase_confirmation_email(request.user.email, request.user.first_name, order, received_total)
        print("Purchase confirmation email sent.")

        # Return order status based on the 'status' field
        print(f"Order processing complete. Returning status: {order.status}")
        return Response({'order_status': order.status, 'redirect': '/'}, status=status.HTTP_200_OK)

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
        
        if round(float(total), 2) == round(float(order.get_cart_total), 2): # Compare floats carefully
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

        response = Response({'order_status': order.complete, 'redirect': '/'}, status=status.HTTP_200_OK)
        response.delete_cookie('cart') # Clear the cart cookie after successful unauthenticated order
        return response

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
    Uses BuyerSupplierInventorySerializer for buyers to hide supplier quantity.
    """
    # serializer_class is now determined dynamically
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        organization = user.organization

        if organization and organization.organization_type in ['buyer', 'both']:
            # Buyers use a serializer that hides supplier quantity and product cost
            return BuyerSupplierInventorySerializer
        else:
            # Suppliers/Internal users use the standard serializer
            return InventorySerializer

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Inventory.objects.none()

        # Prefetch related product and location for efficiency
        queryset = Inventory.objects.select_related('product', 'location')

        # If the user's organization is a Buyer (or both)
        if organization.organization_type in ['buyer', 'both']:
            # Get IDs of organizations that are accepted suppliers to the buyer's organization
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)

            # Filter inventory where:
            # 1. The inventory item belongs to the buyer's own organization OR
            # 2. The product associated with the inventory item belongs to an accepted supplier organization
            queryset = queryset.filter(
                Q(organization=organization) | Q(product__organization__id__in=accepted_supplier_ids)
            )

        # If the user's organization is a Supplier (or both) or Internal
        elif organization.organization_type in ['supplier', 'internal']:
             # Suppliers/Internal users see their own inventory
             queryset = queryset.filter(organization=organization)

        else:
            # Other organization types might have different access rules
            queryset = Inventory.objects.none()

        return queryset.order_by('product__name', 'location__name')

class InventoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific inventory item, ensuring the user's organization
    has access based on relationships.
    Uses BuyerSupplierInventorySerializer for buyers to hide supplier quantity.
    """
    # serializer_class is now determined dynamically
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_serializer_class(self):
        user = self.request.user
        organization = user.organization

        if organization and organization.organization_type in ['buyer', 'both']:
            # Buyers use a serializer that hides supplier quantity and product cost
            return BuyerSupplierInventorySerializer
        else:
            # Suppliers/Internal users use the standard serializer
            return InventorySerializer

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

            # Filter inventory where:
            # 1. The inventory item belongs to the buyer's own organization OR
            # 2. The product associated with the inventory item belongs to an accepted supplier organization
            queryset = queryset.filter(
                Q(organization=organization) | Q(product__organization__id__in=accepted_supplier_ids)
            )

        elif organization.organization_type in ['supplier', 'internal']:
             queryset = queryset.filter(product__organization=organization)

        else:
            queryset = Inventory.objects.none()

        return queryset

class InventoryCreateView(generics.CreateAPIView):
    """
    Allows users from supplier, 'both', 'internal', or 'buyer' organizations
    to create new inventory items for their own organization.
    Creates an InventoryMovement record for the initial stock.
    """
    queryset = Inventory.objects.all()
    serializer_class = InventoryCreateSerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]

    def perform_create(self, serializer):
        user = self.request.user
        organization = user.organization

        # Allow creation if the user's organization is supplier, both, internal, OR buyer
        if organization and organization.organization_type in ['supplier', 'both', 'internal', 'buyer']:
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
    Allows users from supplier, 'both', 'internal', or 'buyer' organizations
    to update inventory quantity for items belonging to their own organization.
    Ensures the inventory item belongs to the user's organization.
    Creates an InventoryMovement record for the change.
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Inventory.objects.none()

        # Users from supplier, both, internal, OR buyer organizations
        # should be able to update inventory items belonging to THEIR OWN organization.
        if organization.organization_type in ['supplier', 'both', 'internal', 'buyer']:
             # Filter inventory items where the inventory's organization matches the user's organization
             queryset = Inventory.objects.filter(organization=organization)
             return queryset
        else:
            # Other organization types are not authorized to update inventory via this view
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
            # Buyers see movements for inventory items belonging to:
            # 1. Their own organization OR
            # 2. Products from organizations they have an 'accepted' supplier relationship with.
            accepted_supplier_ids = OrganizationRelationship.objects.filter(
                buyer_organization=organization,
                status='accepted'
            ).values_list('supplier_organization__id', flat=True)

            queryset = queryset.filter(
                Q(inventory__organization=organization) | Q(inventory__product__organization__id__in=accepted_supplier_ids)
            )

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
    Allows users from supplier, 'both', 'internal', or 'buyer' organizations
    to create new products for their own organization.
    """
    queryset = Product.objects.all()
    serializer_class = ProductCreateSerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]

    def perform_create(self, serializer):
        user = self.request.user
        organization = user.organization
        # Allow creation if the user's organization is supplier, both, internal, OR buyer
        if organization and organization.organization_type in ['supplier', 'both', 'internal', 'buyer']:
            serializer.save(organization=organization)
        else:
            raise serializers.ValidationError("Your organization type is not authorized to create products.")

class BrandListView(generics.ListCreateAPIView):
    """
    Lists and allows creation of Brands for the authenticated user's organization.
    Accessible to users from supplier, 'both', 'internal', or 'buyer' organizations
    with IsAdminOrManager or IsBuyer permissions.
    """
    serializer_class = BrandSerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]

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
        # Allow creation if the user's organization is supplier, both, internal, OR buyer
        if organization and organization.organization_type in ['supplier', 'both', 'internal', 'buyer']:
            serializer.save(organization=organization)
        else:
            # This validation is also handled by permission_classes, but good to have here too.
            raise serializers.ValidationError("Your organization type is not authorized to create brands.")

class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a specific Brand belonging to the
    authenticated user's organization.
    Accessible to users from supplier, 'both', 'internal', or 'buyer' organizations
    with IsAdminOrManager or IsBuyer permissions.
    """
    serializer_class = BrandSerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]
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
    Accessible to users from supplier, 'both', 'internal', or 'buyer' organizations
    with IsAdminOrManager or IsBuyer permissions.
    """
    serializer_class = CategorySerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]

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
        # Allow creation if the user's organization is supplier, both, internal, OR buyer
        if organization and organization.organization_type in ['supplier', 'both', 'internal', 'buyer']:
            serializer.save(organization=organization)
        else:
            # This validation is also handled by permission_classes, but good to have here too.
            raise serializers.ValidationError("Your organization type is not authorized to create categories.")

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a specific Category belonging to the
    authenticated user's organization.
    Accessible to users from supplier, 'both', 'internal', or 'buyer' organizations
    with IsAdminOrManager or IsBuyer permissions.
    """
    serializer_class = CategorySerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]
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
    Accessible to users from supplier, 'both', 'internal', or 'buyer' organizations
    with IsAdminOrManager or IsBuyer permissions.
    """
    serializer_class = LocationSerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]

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
        # Allow creation if the user's organization is supplier, both, internal, OR buyer
        if organization and organization.organization_type in ['supplier', 'both', 'internal', 'buyer']:
            serializer.save(organization=organization)
        else:
            # This validation is also handled by permission_classes, but good to have here too.
            raise serializers.ValidationError("Your organization type is not authorized to create locations.")

class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a specific Location belonging to the
    authenticated user's organization.
    Accessible to users from supplier, 'both', 'internal', or 'buyer' organizations
    with IsAdminOrManager or IsBuyer permissions.
    """
    serializer_class = LocationSerializer
    # Allow IsBuyer OR IsAdminOrManager
    permission_classes = [IsAuthenticated, IsBuyer | IsAdminOrManager]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        organization = user.organization

        if not organization:
            return Location.objects.none()

        # Only allow access to locations belonging to the user's organization
        return Location.objects.filter(organization=organization)