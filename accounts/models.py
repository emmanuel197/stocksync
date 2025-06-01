from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        user = self.create_user(email, username, password=password, **extra_fields)
        user.is_admin = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    username = models.CharField(max_length=30, unique=True, default="JohnDoe123")
    # name = models.CharField(max_length=100, default='John Doe')
    first_name = models.CharField(max_length=255, default='John')
    last_name = models.CharField(max_length=255, default='Doe')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # print(f"User Permissions: {self.get_all_permissions()}")
        
        # Check if the user has the required permission to view a custom user
        required_permission = "accounts.view_user"
        return self.is_active or self.user_permissions.filter(codename=required_permission).exists()

    @property
    def is_superuser(self):
        return self.is_admin

    @is_superuser.setter
    def is_superuser(self, value):
        self.is_admin = value

    @property
    def is_staff(self):
        return self.is_admin
