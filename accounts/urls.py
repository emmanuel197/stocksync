from django.urls import path
from . import views

urlpatterns = [
    path('organization-count/', views.organization_count_view, name='organization_count'),
]
