from django.db import models
from django.db.models import Q
from accounts.request_middleware import get_current_organization, _thread_locals # Import _thread_locals
from contextlib import contextmanager

@contextmanager
def set_current_organization(organization):
    """Context manager to temporarily set the current organization for testing."""
    # Create a mock request object and set the organization on it
    class MockRequest:
        def __init__(self, organization):
            self.organization = organization
            
    mock_request = MockRequest(organization)
    
    original_request = getattr(_thread_locals, 'request', None)
    _thread_locals.request = mock_request
    try:
        yield
    finally:
        if original_request is None:
            if hasattr(_thread_locals, 'request'):
                del _thread_locals.request
        else:
            _thread_locals.request = original_request


class OrganizationModelManager(models.Manager):
    """
    Custom manager that automatically filters querysets by organization.
    
    This manager should be used for all models that have an organization field to
    enforce data isolation between organizations.
    """
    
    def get_queryset(self):
        """Get queryset filtered by organization if applicable"""
        queryset = super().get_queryset()
        
        # Check if model has organization field
        if not hasattr(self.model, 'organization'):
            return queryset
        
        # Get current organization from thread-local request
        organization = get_current_organization()
        
        # If we have an organization, filter by it
        if organization:
            return queryset.filter(organization=organization)
        
        # Otherwise return unfiltered queryset
        return queryset
    
    def create(self, **kwargs):
        """Create a new object, automatically setting organization if not provided"""
        if 'organization' not in kwargs:
            organization = get_current_organization()
            if organization:
                kwargs['organization'] = organization
        
        return super().create(**kwargs)
    
    def get_by_natural_key(self, *args, **kwargs):
        """Override to ensure organization filtering"""
        # Add organization to lookup if applicable
        organization = get_current_organization()
        if organization and hasattr(self.model, 'organization'):
            kwargs['organization'] = organization
            
        return super().get_by_natural_key(*args, **kwargs)


class TenantAwareQuerySet(models.QuerySet):
    """
    A QuerySet that is tenant-aware.
    
    This ensures that all operations on the queryset automatically
    filter by the current organization.
    """
    
    def _filter_by_organization(self, kwargs):
        """Filter by organization if applicable and not already filtered"""
        if hasattr(self.model, 'organization') and 'organization' not in kwargs:
            organization = get_current_organization()
            if organization:
                kwargs['organization'] = organization
        return kwargs
    
    def create(self, **kwargs):
        """Create with organization filtering"""
        kwargs = self._filter_by_organization(kwargs)
        return super().create(**kwargs)
    
    def get_or_create(self, defaults=None, **kwargs):
        """Get or create with organization filtering"""
        if defaults is None:
            defaults = {}
        kwargs = self._filter_by_organization(kwargs)
        defaults = self._filter_by_organization(defaults)
        return super().get_or_create(defaults=defaults, **kwargs)
    
    def update_or_create(self, defaults=None, **kwargs):
        """Update or create with organization filtering"""
        if defaults is None:
            defaults = {}
        kwargs = self._filter_by_organization(kwargs)
        defaults = self._filter_by_organization(defaults)
        return super().update_or_create(defaults=defaults, **kwargs)


class BaseTenantManager(models.Manager):
    """
    Base manager for tenant-aware models.
    
    This manager uses TenantAwareQuerySet to ensure that all operations
    are filtered by the current organization.
    """
    
    def get_queryset(self):
        queryset = TenantAwareQuerySet(self.model, using=self._db)
        # Apply organization filtering here
        request = getattr(_thread_locals, 'request', None) # Get request from thread locals
        organization = None
        if request and hasattr(request, 'organization'):
            organization = request.organization

        if organization and hasattr(self.model, 'organization'):
            return queryset.filter(organization=organization)
        return queryset
    
    def create(self, **kwargs):
        """Create a new object, automatically setting organization if not provided"""
        if hasattr(self.model, 'organization') and 'organization' not in kwargs:
            organization = get_current_organization()
            if organization:
                kwargs['organization'] = organization
        return super().create(**kwargs)
    
    def get_by_natural_key(self, *args, **kwargs):
        """Override to ensure organization filtering"""
        # Add organization to lookup if applicable
        organization = get_current_organization()
        if organization and hasattr(self.model, 'organization'):
            kwargs['organization'] = organization
            
        return super().get_by_natural_key(*args, **kwargs)
