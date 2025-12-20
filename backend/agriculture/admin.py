from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import RiceField, YieldEstimation, SaleNotification

# 1. ตั้งค่าการแสดงผลตาราง "แปลงนา"
@admin.register(RiceField)
class RiceFieldAdmin(GISModelAdmin):
    # เพิ่ม variety ให้เห็นพันธุ์ข้าวด้วย
    list_display = ('name', 'owner', 'district', 'area_rai', 'variety', 'created_at') 
    list_filter = ('district', 'variety', 'created_at') 
    search_fields = ('name', 'owner__username')

# 2. ตั้งค่าการแสดงผลตาราง "การประเมินผลผลิต"
@admin.register(YieldEstimation)
class YieldEstimationAdmin(admin.ModelAdmin):
    list_display = ('field', 'ndvi_mean', 'estimated_yield_ton', 'created_at')
    list_filter = ('created_at',)

# 3. ✅ เพิ่มตาราง "รายการแจ้งขาย" (SaleNotification)
@admin.register(SaleNotification)
class SaleNotificationAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'rice_field', 'quantity_ton', 'price_per_ton', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('farmer__username', 'rice_field__name', 'phone')
    list_editable = ('status',)