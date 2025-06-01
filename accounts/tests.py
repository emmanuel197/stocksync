from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Organization
from accounts.managers import BaseTenantManager, TenantAwareQuerySet, set_current_organization # Import set_current_organization

User = get_user_model()

class TenantManagerTests(TestCase):

    def setUp(self):
        self.org1 = Organization.objects.create(name='Organization 1')
        self.org2 = Organization.objects.create(name='Organization 2')
        # Use User.objects directly as UserManager now has create_user/superuser methods
        self.user1 = User.objects.create_user(
            email='user1@org1.com',
            username='user1_org1',
            password='password',
            organization=self.org1
        )
        self.user2 = User.objects.create_user(
            email='user2@org2.com',
            username='user2_org2',
            password='password',
            organization=self.org2
        )
        # Create superuser without setting organization initially, it will get the default
        self.superuser = User.objects.create_superuser(
            email='superuser@admin.com',
            username='superuser',
            password='password'
        )

    def test_tenant_manager_filters_by_organization(self):
        # Test that queries are filtered by the organization set in the context
        with set_current_organization(self.org1): # Use the context manager
            self.assertEqual(Organization.objects.all().count(), 1)
            self.assertEqual(Organization.objects.all().first(), self.org1)
            
        with set_current_organization(self.org2): # Use the context manager
            self.assertEqual(Organization.objects.all().count(), 1)
            self.assertEqual(Organization.objects.all().first(), self.org2)

    def test_superuser_sees_all_organizations(self):
        # Test that a superuser sees all organizations (bypassing tenant filtering)
        # Use the model's internal _base_manager to get an unfiltered count
        self.assertEqual(Organization._base_manager.count(), 3) # Expect 3 including the default admin org

    # Add more tests for other models using TenantManager
    # For example, test filtering for Products, Orders, etc.

class OrganizationModelTests(TestCase):

    def test_organization_creation(self):
        org = Organization.objects.create(name='Test Org')
        self.assertEqual(org.name, 'Test Org')
        self.assertTrue(org.active_status)

    # Add more tests for Organization model methods and properties

class UserModelTests(TestCase):

    def test_user_creation(self):
        org = Organization.objects.create(name='Test Org')
        user = User.objects.create_user(
            email='testuser@testorg.com',
            username='testuser',
            password='password',
            organization=org
        )
        self.assertEqual(user.email, 'testuser@testorg.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertEqual(user.organization, org)

    def test_superuser_creation(self):
        superuser = User.objects.create_superuser(
            email='testadmin@admin.com',
            username='testadmin',
            password='password'
        )
        self.assertEqual(superuser.email, 'testadmin@admin.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_admin)
        self.assertTrue(superuser.is_superuser)
        # Superuser should be associated with the default organization
        self.assertIsNotNone(superuser.organization)

    # Add more tests for User model methods and properties
