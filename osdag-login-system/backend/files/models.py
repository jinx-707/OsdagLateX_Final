import os
import hashlib
import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


def user_directory_path(instance, filename):
    return f'user_{instance.owner.id}/{filename}'


class OsdagFile(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_files'
    )
    file = models.FileField(upload_to=user_directory_path)
    filename = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    file_size = models.BigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.filename} (owned by {self.owner.username})"

    def compute_hash(self):
        hasher = hashlib.sha256()
        self.file.seek(0)
        for chunk in self.file.chunks():
            hasher.update(chunk)
        self.file.seek(0)
        return hasher.hexdigest()

    def save(self, *args, **kwargs):
        if self.file:
            if not self.sha256:
                self.sha256 = self.compute_hash()
            if not self.file_size:
                self.file_size = self.file.size
        if not self.filename:
            self.filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)


class FileAccess(models.Model):
    class Permission(models.TextChoices):
        VIEW = 'view', 'View'
        EDIT = 'edit', 'Edit'

    file = models.ForeignKey(
        OsdagFile,
        on_delete=models.CASCADE,
        related_name='access_grants'
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_access_grants'
    )
    permission = models.CharField(
        max_length=10,
        choices=Permission.choices,
        default=Permission.VIEW
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Leave empty for permanent access"
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file', 'shared_with')

    def __str__(self):
        return f"{self.shared_with.username} -> {self.permission} on {self.file.filename}"

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        expires = self.expires_at
        if isinstance(expires, str):
            from django.utils.dateparse import parse_datetime
            expires = parse_datetime(expires)
            if expires is None:
                return False
        return timezone.now() > expires


class FileAccessLog(models.Model):
    class Action(models.TextChoices):
        VIEW = 'view', 'View'
        DOWNLOAD = 'download', 'Download'
        SHARE = 'share', 'Share'

    file = models.ForeignKey(
        OsdagFile,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username} -> {self.action} on {self.file.filename} at {self.timestamp}"


class Team(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_teams'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MagicLink(models.Model):
    file = models.ForeignKey(
        OsdagFile,
        on_delete=models.CASCADE,
        related_name='magic_links'
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_magic_links'
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MagicLink({self.token[:8]}...) -> {self.file.filename}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
