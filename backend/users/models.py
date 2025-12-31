from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'ผู้ดูแลระบบ'),
        ('FARMER', 'เกษตรกร'),
        ('MILLER', 'โรงสี/ผู้รับซื้อ'),
        ('GOVT', 'เจ้าหน้าที่รัฐ'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='FARMER')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    line_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Line ID")
    address = models.TextField(blank=True, null=True, verbose_name="ที่อยู่ / ที่ตั้งแปลงนา")
    about_me = models.TextField(blank=True, null=True, verbose_name="เกี่ยวกับฉัน")

    REQUIRED_FIELDS = ['email', 'role']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"