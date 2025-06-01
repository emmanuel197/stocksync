from django.shortcuts import render
from django.http import JsonResponse
from .models import Organization

def organization_count_view(request):
    """A simple view to return the count of organizations visible to the current user."""
    count = Organization.objects.count()
    return JsonResponse({'count': count})
