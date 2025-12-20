from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('farmer', 'เกษตรกร'),
        ('mill', 'โรงสี'),
        ('admin', 'ผู้ดูแลระบบ'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='farmer')