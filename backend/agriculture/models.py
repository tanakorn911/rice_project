from django.contrib.gis.db import models
from django.conf import settings

class RiceField(models.Model):
    # --- 1. ความสัมพันธ์และข้อมูลหลัก ---
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rice_fields')
    name = models.CharField(max_length=100, help_text="ชื่อแปลงนา")
    is_active = models.BooleanField(default=True)
    
    # --- 2. ข้อมูลเชิงพื้นที่ (Spatial Data) ---
    boundary = models.PolygonField(help_text="ขอบเขตแปลงนา (Polygon)")
    area_rai = models.FloatField(default=0.0, help_text="พื้นที่ (ไร่)")
    district = models.CharField(max_length=100, default='Phayao', help_text="จังหวัด/อำเภอ/ตำบล")
    
    # --- 3. ข้อมูลทางการเกษตร ---
    VARIETY_CHOICES = [
        ('KDML105', 'หอมมะลิ 105'),
        ('RD6', 'กข 6 (ข้าวเหนียว)'),
        ('RD15', 'กข 15'),
        ('PATHUM1', 'ปทุมธานี 1'),
        ('OTHER', 'อื่นๆ'),
    ]
    variety = models.CharField(max_length=20, choices=VARIETY_CHOICES, default='KDML105')

    # --- 4. System Fields (สำคัญมากสำหรับ Soft Delete) ---
    is_active = models.BooleanField(default=True, help_text="True=แสดงผล, False=ถูกลบ(Soft Delete)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # เพิ่มเพื่อดูการแก้ไขล่าสุด

    class Meta:
        # เอา unique_together ออก เพื่อให้สามารถสร้างชื่อซ้ำได้ถ้าอันเก่าถูก Soft Delete ไปแล้ว
        # unique_together = ('owner', 'name') 
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.owner} ({'Active' if self.is_active else 'Deleted'})"

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
    negotiated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="ราคาที่โรงสีต่อรอง")
    phone = models.CharField(max_length=20, help_text="เบอร์ติดต่อชาวนา")
    
    status = models.CharField(max_length=20, default='OPEN', choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    buyer_contact = models.CharField(max_length=20, blank=True, null=True, help_text="เบอร์ติดต่อคนซื้อ")
    sold_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.farmer} - {self.status}"