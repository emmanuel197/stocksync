from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Organization
from accounts.managers import TenantManager

User = get_user_model()

class TenantManagerTests(TestCase):

    def setUp(self):
        self.org1 = Organization.objects.create(name='Organization 1')
        self.org2 = Organization.objects.create(name='Organization 2')
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
        self.superuser = User.objects.create_superuser(
            email='superuser@admin.com',
            username='superuser',
            password='password'
        )

    def test_tenant_manager_filters_by_organization(self):
        # Test that a regular user only sees objects from their organization
        with self.settings(AUTH_USER_MODEL='accounts.User'):
            self.client.force_login(self.user1)
            self.assertEqual(Organization.objects.count(), 1)
            self.assertEqual(Organization.objects.first(), self.org1)
            
            self.client.force_login(self.user2)
            self.assertEqual(Organization.objects.count(), 1)
            self.assertEqual(Organization.objects.first(), self.org2)

    def test_superuser_sees_all_organizations(self):
        # Test that a superuser sees objects from all organizations
        with self.settings(AUTH_USER_MODEL='accounts.User'):
            self.client.force_login(self.superuser)
            self.assertEqual(Organization.objects.count(), 2)

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
