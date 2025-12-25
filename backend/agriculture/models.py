from django.contrib.gis.db import models
from django.conf import settings

class RiceField(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    boundary = models.PolygonField()
    area_rai = models.FloatField()
    district = models.CharField(max_length=100, default='Phayao')
    created_at = models.DateTimeField(auto_now_add=True)

    VARIETY_CHOICES = [
        ('KDML105', 'หอมมะลิ 105'),
        ('RD6', 'กข 6 (ข้าวเหนียว)'),
        ('RD15', 'กข 15'),
        ('PATHUM1', 'ปทุมธานี'),
        ('OTHER', 'อื่นๆ'),
    ]
    variety = models.CharField(max_length=20, choices=VARIETY_CHOICES, default='KDML105')

    class Meta:
        unique_together = ('owner', 'name')

    def __str__(self):
        return f"{self.name} - {self.owner}"

class YieldEstimation(models.Model):
    field = models.ForeignKey(RiceField, on_delete=models.CASCADE)
    ndvi_mean = models.FloatField()
    estimated_yield_ton = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

class SaleNotification(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'รอรับซื้อ'),
        ('REQUESTED', 'รออนุมัติ'), 
        ('SOLD', 'ขายแล้ว'),
    ]

    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales')
    rice_field = models.ForeignKey(RiceField, on_delete=models.CASCADE)
    quantity_ton = models.FloatField(help_text="จำนวนตันที่ต้องการขาย")
    price_per_ton = models.DecimalField(max_digits=10, decimal_places=2, help_text="ราคาที่ต้องการ (บาท/ตัน)")
    phone = models.CharField(max_length=20, help_text="เบอร์ติดต่อชาวนา")
    
    status = models.CharField(max_length=20, default='OPEN', choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    buyer_contact = models.CharField(max_length=20, blank=True, null=True, help_text="เบอร์ติดต่อคนซื้อ")
    sold_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.farmer} - {self.status}"