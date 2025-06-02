import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class Organization(models.Model):
    ORGANIZATION_TYPE_CHOICES = [
        ('buyer', 'Buyer Organization'),
        ('supplier', 'Supplier Organization'),
        ('both', 'Buyer and Supplier Organization'),
        ('internal', 'Internal Organization'),
    ]

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
    organization_type = models.CharField(max_length=20, choices=ORGANIZATION_TYPE_CHOICES, default='buyer')
    active_status = models.BooleanField(default=False)
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['active_status']),
            models.Index(fields=['activation_token']),
            models.Index(fields=['organization_type']),
        ]

    def __str__(self):
        return self.name


class OrganizationRelationship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    buyer_organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='buying_relationships',
        limit_choices_to={'organization_type__in': ['buyer', 'both']}
    )
    supplier_organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='supplying_relationships',
        limit_choices_to={'organization_type__in': ['supplier', 'both']}
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    initiated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='initiated_relationships')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('buyer_organization', 'supplier_organization')
        indexes = [
            models.Index(fields=['buyer_organization', 'supplier_organization']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.buyer_organization.name} buys from {self.supplier_organization.name} ({self.status})"


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, username, password=None, organization=None, role='staff', **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        if not username:
            raise ValueError(_('The Username must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, organization=organization, role=role, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        extra_fields.pop('organization', None)

        return self.create_user(email, username, password, organization=None, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]

    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as active. '
                   'Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_admin(self):
        return self.is_superuser or self.role == 'admin'
