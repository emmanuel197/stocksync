from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Custom permission to only allow admin users to access an object."""

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users.
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsManager(permissions.BasePermission):
    """Custom permission to only allow manager users to access an object."""

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to manager users.
        return request.user and request.user.is_authenticated and request.user.role == 'manager'

class IsStaff(permissions.BasePermission):
    """Custom permission to only allow staff users to access an object."""

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to staff users.
        return request.user and request.user.is_authenticated and request.user.role == 'staff'

class IsBuyer(permissions.BasePermission):
    """Custom permission to only allow buyer users to access an object."""

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to users associated with a 'buyer' organization.
        user = request.user
        # Check if user is authenticated and has an organization linked
        if user and user.is_authenticated and hasattr(user, 'organization') and user.organization:
            # Check if the organization type is 'buyer' or 'both' (if 'both' should also have buyer permissions)
            return user.organization.organization_type in ['buyer', 'both']
        return False

class IsSupplier(permissions.BasePermission):
    """Custom permission to only allow supplier users to access an object."""

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to supplier users.
        return request.user and request.user.is_authenticated and request.user.role == 'supplier'

class IsDriver(permissions.BasePermission):
    """Custom permission to only allow driver users to access an object."""

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to driver users.
        return request.user and request.user.is_authenticated and request.user.role == 'driver'

class IsAdminOrManager(permissions.BasePermission):
    """Custom permission to only allow admin or manager users to access an object."""

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin or manager users.
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'manager']

class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of an object or admin users to access it."""

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object or admin users.
        return obj.owner == request.user or (request.user and request.user.is_authenticated and request.user.role == 'admin')
