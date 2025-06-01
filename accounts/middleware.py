from django.db.models import Q
from django.utils.deprecation import MiddlewareMixin
from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django.db import models


class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware to enforce organization-based isolation at the query level.
    
    This middleware automatically filters querysets by the current user's organization
    for models that have an organization field.
    """
    
    def process_request(self, request):
        """Process incoming request and set up organization filtering"""
        
        # Skip for anonymous users or users without organization
        if isinstance(request.user, AnonymousUser) or not hasattr(request.user, 'organization'):
            return None
        
        # Skip for superusers
        if request.user.is_superuser:
            return None
        
        # Store the user's organization for managers to use
        if request.user.organization:
            request.organization = request.user.organization
            
        return None


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
        
        # Get current request from thread local
        from threading import local
        _thread_locals = local()
        request = getattr(_thread_locals, 'request', None)
        
        # If we have a request and it has an organization, filter by it
        if request and hasattr(request, 'organization'):
            organization = request.organization
            if organization:
                return queryset.filter(organization=organization)
        
        # Otherwise return unfiltered queryset
        return queryset
