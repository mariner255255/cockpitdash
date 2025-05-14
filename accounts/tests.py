from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

@override_settings(
    ACCOUNT_EMAIL_VERIFICATION='none',  # Disable email verification for tests
    ACCOUNT_RATE_LIMITS=False          # Disable rate limiting for tests
)
class AccountTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_creation(self):
        """Test user creation"""
        user_count = get_user_model().objects.count()
        self.assertEqual(user_count, 1)
        self.assertEqual(self.user.username, 'testuser')

    def test_login_view(self):
        """Test login view"""
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
          # Test login with allauth
        response = self.client.post(reverse('account_login'), {
            'login': 'test@example.com',  # Use email since we configured email authentication
            'password': 'testpass123'
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_profile_view(self):
        """Test profile view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

    def test_registration(self):
        """Test user registration"""
        response = self.client.post(reverse('account_signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newuserpass123',
            'password2': 'newuserpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 2)
        new_user = get_user_model().objects.get(username='newuser')
        self.assertEqual(new_user.email, 'newuser@example.com')
