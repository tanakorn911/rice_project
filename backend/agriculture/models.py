from django.contrib.gis.db import models
from django.conf import settings

class RiceField(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    boundary = models.PolygonField()
    area_rai = models.FloatField()
    district = models.CharField(max_length=100, default='Phayao')
    created_at = models.DateTimeField(auto_now_add=True)

    # เพิ่มตัวเลือกพันธุ์ข้าว
    VARIETY_CHOICES = [
        ('KDML105', 'หอมมะลิ 105'),
        ('RD6', 'กข 6 (ข้าวเหนียว)'),
        ('RD15', 'กข 15'),
        ('PATHUM1', 'ปทุมธานี 1'),
        ('OTHER', 'อื่นๆ'),
    ]
    variety = models.CharField(max_length=20, choices=VARIETY_CHOICES, default='KDML105')

    def __str__(self):
        return f"{self.name} - {self.owner}"

class YieldEstimation(models.Model):
    field = models.ForeignKey(RiceField, on_delete=models.CASCADE)
    ndvi_mean = models.FloatField()
    estimated_yield_ton = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

class SaleNotification(models.Model):
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rice_field = models.ForeignKey(RiceField, on_delete=models.CASCADE)
    quantity_ton = models.FloatField(help_text="จำนวนตันที่ต้องการขาย")
    price_per_ton = models.DecimalField(max_digits=10, decimal_places=2, help_text="ราคาที่ต้องการ (บาท/ตัน)")
    phone = models.CharField(max_length=20, help_text="เบอร์ติดต่อ")
    status = models.CharField(max_length=20, default='OPEN', choices=[('OPEN', 'รอรับซื้อ'), ('CLOSED', 'ขายแล้ว')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farmer} ขาย {self.quantity_ton} ตัน"