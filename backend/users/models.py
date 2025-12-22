from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('FARMER', 'เกษตรกร'),
        ('MILLER', 'โรงสี/ผู้รับซื้อ'),
        ('GOVT', 'เจ้าหน้าที่รัฐ'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='FARMER')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"