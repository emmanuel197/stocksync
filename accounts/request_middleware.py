from threading import local

_thread_locals = local() # Define _thread_locals here

def get_current_request():
    """
    Get the current request from thread-local storage.
    
    This allows models and managers to access the current request
    for organization filtering and other context-aware behavior.
    """
    return getattr(_thread_locals, 'request', None)

def get_current_organization():
    """
    Get the organization from the current request.
    
    Returns None if there is no request or no organization.
    """
    request = get_current_request()
    if request and hasattr(request, 'organization'):
        return request.organization
    return None


class RequestMiddleware:
    """
    Middleware to store the current request in thread-local storage.
    
    This allows organization filtering to work in model managers by
    providing access to the current request and organization.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Store request in thread-local storage
        _thread_locals.request = request
        
        # Process the request
        response = self.get_response(request)
        
        # Clean up thread-local storage
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
            
        return response
