# filepath: c:\Users\eamok\OneDrive\Desktop\js files\kuandorwear\accounts\signals.py
from django.dispatch import receiver
from djoser.signals import user_activated
from .models import Organization, User

@receiver(user_activated)
def activate_organization_on_user_activation(sender, user, request, **kwargs):
    """
    Signal receiver to activate the user's organization when the user is activated by Djoser.
    """
    if user.organization and not user.organization.active_status:
        user.organization.active_status = True
        user.organization.save(update_fields=['active_status'])
        print(f"Organization {user.organization.name} activated by user {user.email} activation.")
