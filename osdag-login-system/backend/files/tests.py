from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
import time
from .models import OsdagFile, FileAccess, FileAccessLog, Team

User = get_user_model()


class FilePermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(
            username='alice', email='alice@test.com', password='pass'
        )
        self.bob = User.objects.create_user(
            username='bob', email='bob@test.com', password='pass'
        )
        self.carol = User.objects.create_user(
            username='carol', email='carol@test.com', password='pass'
        )

        self.client.force_authenticate(user=self.alice)
        test_file = SimpleUploadedFile('test.txt', b'Hello World')
        response = self.client.post('/api/files/', {'file': test_file, 'description': 'test'})
        self.file_id = response.data['id']
        self.client.force_authenticate(user=None)

    def test_bob_cannot_download_before_share(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/files/{self.file_id}/download/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_alice_can_share_with_bob(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(FileAccess.objects.filter(
            file_id=self.file_id, shared_with=self.bob
        ).exists())

    def test_bob_can_download_after_share(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view'}
        )
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/files/{self.file_id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_carol_cannot_download_even_after_share(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view'}
        )
        self.client.force_authenticate(user=self.carol)
        response = self.client.get(f'/api/files/{self.file_id}/download/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_bob_cannot_share_alices_file(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view'}
        )
        self.client.force_authenticate(user=self.bob)
        response = self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'carol@test.com', 'permission': 'view'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bob_cannot_delete_alices_file(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view'}
        )
        self.client.force_authenticate(user=self.bob)
        response = self.client.delete(f'/api/files/{self.file_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_expiry_works(self):
        self.client.force_authenticate(user=self.alice)
        expires_at = timezone.now() + timedelta(seconds=3)
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view', 'expires_at': expires_at.isoformat()}
        )
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/files/{self.file_id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        time.sleep(4)
        response = self.client.get(f'/api/files/{self.file_id}/download/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_revoke_works(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view'}
        )
        self.client.post(
            f'/api/files/{self.file_id}/revoke/',
            {'user_id': self.bob.id}
        )
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/files/{self.file_id}/download/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_team_sharing(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            '/api/teams/',
            {'name': 'Bridge Team', 'member_emails': ['bob@test.com']},
            format='json'
        )
        team_id = response.data['id']
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'team_id': team_id, 'permission': 'view'}
        )
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/files/{self.file_id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_audit_log(self):
        self.client.force_authenticate(user=self.alice)
        self.client.post(
            f'/api/files/{self.file_id}/share/',
            {'email': 'bob@test.com', 'permission': 'view'}
        )
        self.client.force_authenticate(user=self.bob)
        self.client.get(f'/api/files/{self.file_id}/download/')

        self.client.force_authenticate(user=self.alice)
        response = self.client.get(f'/api/files/{self.file_id}/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/files/{self.file_id}/logs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sha256_hash(self):
        self.client.force_authenticate(user=self.alice)
        file_obj = OsdagFile.objects.get(id=self.file_id)
        self.assertEqual(file_obj.sha256, file_obj.compute_hash())
