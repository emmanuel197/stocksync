from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from accounts.managers import TenantManager # Import TenantManager


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='organization_logos/', null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    subscription_plan = models.CharField(
        max_length=50, 
        default='free',
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise')
        ]
    )
    active_status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = TenantManager() # Use TenantManager

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['active_status']),
        ]
        
    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        # Set default organization if not provided
        if 'organization' not in extra_fields or extra_fields['organization'] is None:
            # This will be used only if Organization exists, otherwise will be None
            try:
                default_org = Organization.objects.filter(active_status=True).first()
                if default_org:
                    extra_fields['organization'] = default_org
            except:
                pass
                
        user = self.model(
            email=self.normalize_email(email), 
            username=username, 
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        # For superuser, try to get or create a default organization
        try:
            organization, _ = Organization.objects.get_or_create(
                name='System Administration',
                defaults={
                    'subscription_plan': 'enterprise',
                }
            )
            extra_fields['organization'] = organization
        except:
            # If we're running migrations, Organization table might not exist yet
            pass
            
        user = self.create_user(email, username, password=password, **extra_fields)
        user.role = 'admin'
        user.is_admin = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    username = models.CharField(max_length=30, unique=True, default="JohnDoe123")
    first_name = models.CharField(max_length=255, default='John')
    last_name = models.CharField(max_length=255, default='Doe')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    
    # New fields for role-based access and multi-tenant support
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    objects = TenantManager() # Use TenantManager

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['organization']),
        ]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # Check if the user has the required permission
        if self.is_admin:
            return True
            
        # Check if the user has the required permission to view a custom user
        required_permission = "accounts.view_user"
        return self.is_active and self.user_permissions.filter(codename=perm.split('.')[1]).exists()
    
    def has_module_perms(self, app_label):
        # Admin users have access to all modules
        return self.is_admin or self.is_active

    @property
    def is_superuser(self):
        return self.is_admin

    @is_superuser.setter
    def is_superuser(self, value):
        self.is_admin = value

    @property
    def is_staff(self):
        return self.is_admin or self.role in ['admin', 'manager']
