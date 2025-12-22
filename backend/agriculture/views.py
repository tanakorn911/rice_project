import os
import json
import datetime
import ee
from google.oauth2 import service_account

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Sum, Count, Q
from django.conf import settings

from .models import RiceField, YieldEstimation, SaleNotification
from .serializers import RiceFieldSerializer, YieldEstimationSerializer, SaleNotificationSerializer

# ==========================================
# 0. GEE Initialization (การเชื่อมต่อระบบดาวเทียม)
# ==========================================
try:
    KEY_PATH = os.path.join(settings.BASE_DIR, 'gee-key.json')
    if os.path.exists(KEY_PATH):
        SCOPES = ['https://www.googleapis.com/auth/earthengine']
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
        ee.Initialize(credentials=credentials)
        print("✅ GEE Initialized Successfully!")
    else:
        ee.Initialize()
        print("⚠️ GEE Initialized (No Key File)")
except Exception as e:
    print(f"❌ GEE Init Error: {e}")

# ==========================================
# 1. ส่วนจัดการหน้าเว็บ (Web Views & Router)
# ==========================================

@login_required
def dashboard_redirect(request):
    """ฟังก์ชันนำทางตามบทบาท (รองรับ Admin สลับหน้าผ่าน ?view=)"""
    user = request.user
    view_as = request.GET.get('view')
    
    if user.is_superuser:
        if view_as == 'miller': return redirect('miller_dashboard')
        if view_as == 'govt': return redirect('govt_dashboard')
        if view_as == 'farmer': return render(request, 'agriculture/dashboard.html')
        return redirect('/admin/')
    
    role = getattr(user, 'role', 'FARMER')
    if role == 'MILLER':
        return redirect('miller_dashboard')
    elif role == 'GOVT':
        return redirect('govt_dashboard')
    else:
        return render(request, 'agriculture/dashboard.html')

@login_required
def miller_dashboard(request): 
    return render(request, 'agriculture/miller_dashboard.html')

@login_required
def govt_dashboard(request): 
    return render(request, 'agriculture/govt_dashboard.html')

# ==========================================
# 2. ส่วน API (Data & Calculation)
# ==========================================

@api_view(['GET'])
@login_required
def dashboard_stats(request):
    """API สรุปข้อมูลสถิติรวม"""
    
    # 1. ดึงเฉพาะการวิเคราะห์ NDVI ที่ "แปลงนา" ยังไม่ถูกลบ
    estimations = YieldEstimation.objects.filter(field__in=RiceField.objects.all())
    
    # 2. คำนวณสถิติสุขภาพข้าว
    h_good = estimations.filter(ndvi_mean__gte=0.5).count()
    h_med = estimations.filter(ndvi_mean__gte=0.3, ndvi_mean__lt=0.5).count()
    h_poor = estimations.filter(ndvi_mean__lt=0.3).count()

    # 3. ข้อมูลสรุปอื่นๆ
    total_fields = RiceField.objects.count()
    total_area = RiceField.objects.aggregate(Sum('area_rai'))['area_rai__sum'] or 0
    total_farmers = RiceField.objects.values('owner').distinct().count()
    total_yield = estimations.aggregate(Sum('estimated_yield_ton'))['estimated_yield_ton__sum'] or 0
    
    # 4. ข้อมูลกราฟพันธุ์ข้าว
    variety_data = RiceField.objects.values('variety').annotate(total=Count('variety'))
    variety_dict = dict(RiceField.VARIETY_CHOICES)
    v_labels = [variety_dict.get(item['variety'], item['variety']) for item in variety_data]
    v_data = [item['total'] for item in variety_data]

    return Response({
        'total_fields': total_fields,
        'total_area': round(total_area, 2),
        'total_farmers': total_farmers,
        'total_yield': round(total_yield, 2),
        'charts': {
            'variety': {'labels': v_labels, 'data': v_data},
            'health': {'data': [h_good, h_med, h_poor]}
        }
    })

class RiceFieldViewSet(viewsets.ModelViewSet):
    """จัดการข้อมูลแปลงนาแบบรายแปลง"""
    serializer_class = RiceFieldSerializer

    def get_queryset(self):
        # ป้องกัน AnonymousUser หลุดเข้ามา
        if not self.request.user.is_authenticated:
            return RiceField.objects.none()

        user = self.request.user
        role = getattr(user, 'role', 'FARMER')
        if user.is_superuser or role in ['MILLER', 'GOVT']:
            return RiceField.objects.all().order_by('-created_at')
        return RiceField.objects.filter(owner=user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """บันทึกข้อมูลแปลงนาพร้อม Geofence ล็อคพิกัดพะเยา"""
        try:
            data = request.data
            geom_input = data.get('geometry')
            if not geom_input: 
                return Response({'error': 'กรุณาวาดแปลงนาบนแผนที่'}, status=400)
            
            if isinstance(geom_input, str): 
                geom_input = json.loads(geom_input)
            
            poly = GEOSGeometry(json.dumps(geom_input))
            
            # 📍 ล็อคพิกัด อ.เมืองพะเยา (99.80 - 100.10 E, 19.00 - 19.35 N)
            centroid = poly.centroid
            # หากต้องการปลดล็อคให้วาดที่ไหนก็ได้ ให้ comment 2 บรรทัดล่างนี้ทิ้ง
            if not (99.80 <= centroid.x <= 100.10 and 19.00 <= centroid.y <= 19.35):
                 return Response({'error': 'อยู่นอกเขตพื้นที่ อ.เมืองพะเยา'}, status=400)
            
            # คำนวณพื้นที่ (ตร.ม. -> ไร่)
            area_sqm = poly.transform(32647, clone=True).area
            area_rai = round(area_sqm / 1600, 2)

            field = RiceField.objects.create(
                owner=request.user,
                name=data.get('name', f'แปลงนา {datetime.date.today()}'),
                boundary=poly,
                area_rai=area_rai,
                variety=data.get('variety', 'KDML105'),
                district='Phayao'
            )
            return Response({'id': field.id, 'area': area_rai}, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def calculate_yield(self, request, pk=None):
        """วิเคราะห์ NDVI และคำนวณผลผลิต (แก้ไขเรื่องเมฆและค่าติดลบแล้ว)"""
        rice_field = self.get_object()
        try:
            geom_json = json.loads(rice_field.boundary.json)
            ee_geometry = ee.Geometry.Polygon(geom_json['coordinates'])
            
            # 🔧 แก้ไข 1: ขยายเวลาเป็น 1 ปี เพื่อให้เจอภาพแน่นอน
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=365)
            
            # 🔧 แก้ไข 2: ใช้ .median() แทน .first() เพื่อตัดเมฆออกอัตโนมัติ
            dataset = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(ee_geometry)
                       .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) # ยอมรับเมฆได้ 60%
                       )
            
            if dataset.size().getInfo() == 0:
                return Response({'error': 'ไม่พบภาพดาวเทียมในช่วงเวลานี้ (เมฆมาก)'}, status=400)

            # ใช้ค่ามัธยฐาน (Median) ตัด Noise และเมฆ
            image = dataset.median()
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            val = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(), 
                geometry=ee_geometry, 
                scale=10,  
                maxPixels=1e9
            ).get('NDVI').getInfo()
            
            if val is None: 
                return Response({'error': 'พื้นที่เล็กเกินไป หรืออยู่นอกขอบเขตภาพ'}, status=400)
            
            # 🔧 แก้ไข 3: ดักจับค่าน้ำ/สิ่งปลูกสร้าง (NDVI < 0.2)
            if val < 0.2:
                yield_ton = 0 # ไม่ใช่พืช ผลผลิตเป็น 0
                note = "พื้นที่น้ำ/สิ่งปลูกสร้าง"
            else:
                # Yield Model: NDVI * 800 (กก./ไร่) / 1000 = ตัน
                yield_ton = (val * 800 * rice_field.area_rai) / 1000
                note = "ปกติ"
            
            YieldEstimation.objects.create(
                field=rice_field, ndvi_mean=val, estimated_yield_ton=yield_ton
            )
            
            return Response({'ndvi': round(val, 4), 'yield_ton': round(yield_ton, 2), 'note': note})

        except Exception as e:
            print(f"GEE Error: {e}")
            return Response({'error': 'ระบบดาวเทียมตอบสนองช้า หรือ Internet ไม่เสถียร'}, status=500)

class SaleNotificationViewSet(viewsets.ModelViewSet):
    """จัดการการแจ้งขายผลผลิต (Marketplace Flow)"""
    serializer_class = SaleNotificationSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SaleNotification.objects.none()

        user = self.request.user
        role = getattr(user, 'role', 'FARMER')
        
        # Farmer: เห็นแค่ของตัวเอง
        if role == 'FARMER':
            return SaleNotification.objects.filter(farmer=user).order_by('-created_at')
        
        # Miller/Govt: เห็นรายการที่เปิดขาย (OPEN) หรือ รายการที่ตัวเองจองไว้
        return SaleNotification.objects.filter(
            Q(status='OPEN') | Q(buyer=user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)

    # 1. โรงสีกดขอซื้อ
    @action(detail=True, methods=['post'])
    def request_buy(self, request, pk=None):
        sale = self.get_object()
        if sale.status != 'OPEN':
            return Response({'error': 'รายการนี้ไม่ว่างขายแล้ว'}, status=400)
        
        sale.status = 'REQUESTED'
        sale.buyer = request.user
        sale.buyer_contact = request.data.get('contact', 'ไม่ระบุ')
        sale.save()
        return Response({'status': 'requested'})

    # 2. ชาวนากดอนุมัติ
    @action(detail=True, methods=['post'])
    def approve_sell(self, request, pk=None):
        sale = self.get_object()
        if sale.farmer != request.user:
            return Response({'error': 'คุณไม่ใช่เจ้าของรายการนี้'}, status=403)
        
        sale.status = 'SOLD'
        sale.save()
        return Response({'status': 'sold'})
    
    # 3. ชาวนากดปฏิเสธ
    @action(detail=True, methods=['post'])
    def reject_sell(self, request, pk=None):
        sale = self.get_object()
        if sale.farmer != request.user:
            return Response({'error': 'คุณไม่ใช่เจ้าของรายการนี้'}, status=403)
        
        sale.status = 'OPEN'
        sale.buyer = None
        sale.buyer_contact = None
        sale.save()
        return Response({'status': 'open'})