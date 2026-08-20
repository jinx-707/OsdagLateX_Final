from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        ENGINEER = 'engineer', _('Engineer')
        ADMIN = 'admin', _('Admin')

    email = models.EmailField(unique=True)
    institution = models.CharField(max_length=255, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
