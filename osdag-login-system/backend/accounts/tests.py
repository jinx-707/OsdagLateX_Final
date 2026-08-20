from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        response = self.client.post('/api/accounts/register/', {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'student',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_username(self):
        User.objects.create_user(username='alice', email='alice@test.com', password='pass123')
        response = self.client.post('/api/accounts/login/', {
            'username': 'alice',
            'password': 'pass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_email(self):
        User.objects.create_user(username='alice', email='alice@test.com', password='pass123')
        response = self.client.post('/api/accounts/login/', {
            'username': 'alice@test.com',
            'password': 'pass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_wrong_password(self):
        User.objects.create_user(username='alice', email='alice@test.com', password='pass123')
        response = self.client.post('/api/accounts/login/', {
            'username': 'alice',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
