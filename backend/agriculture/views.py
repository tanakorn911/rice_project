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
from django.db.models import Sum, Count

from .models import RiceField, YieldEstimation, SaleNotification
from .serializers import RiceFieldSerializer, YieldEstimationSerializer, SaleNotificationSerializer

# ==========================================
# 0. GEE Initialization (การเชื่อมต่อระบบดาวเทียม)
# ==========================================
try:
    KEY_PATH = 'gee-key.json' 
    if os.path.exists(KEY_PATH):
        SCOPES = ['https://www.googleapis.com/auth/earthengine']
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
        ee.Initialize(credentials=credentials)
        print("✅ GEE Initialized Successfully!")
    else:
        ee.Initialize() 
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
    
    # 1. ดึงเฉพาะการวิเคราะห์ NDVI ที่ "แปลงนา" ยังไม่ถูกลบ (Active Fields only)
    estimations = YieldEstimation.objects.filter(field__in=RiceField.objects.all())
    
    # 2. คำนวณสถิติสุขภาพข้าวจากรายการที่กรองแล้ว
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
            if not (99.80 <= centroid.x <= 100.10 and 19.00 <= centroid.y <= 19.35):
                return Response({'error': 'อยู่นอกเขตพื้นที่ อ.เมืองพะเยา'}, status=400)
            
            # คำนวณพื้นที่ (ตร.ม. -> ไร่)
            area_rai = round(poly.transform(32647, clone=True).area / 1600, 2)

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
        """วิเคราะห์ NDVI และคำนวณผลผลิตผ่าน Google Earth Engine (แบบรวดเร็ว)"""
        rice_field = self.get_object()
        try:
            geom_json = json.loads(rice_field.boundary.json)
            ee_geometry = ee.Geometry.Polygon(geom_json['coordinates'])
            
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=30)
            
            # 1. ดึงภาพดาวเทียม (ตัดการเช็ค .size() ออกเพื่อความเร็ว)
            dataset = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(ee_geometry)
                       .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                       .sort('CLOUDY_PIXEL_PERCENTAGE'))
            
            # 2. คำนวณ NDVI
            image = dataset.first()
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            # 3. ดึงค่าเฉลี่ย (ลด scale=20, เพิ่ม maxPixels) ช่วยให้เร็วขึ้นมาก
            val = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(), 
                geometry=ee_geometry, 
                scale=10,  
                maxPixels=1e9
            ).get('NDVI').getInfo()
            
            if val is None: 
                return Response({'error': 'ไม่พบภาพดาวเทียมที่ชัดเจนในช่วงนี้'}, status=400)
            
            # Yield Model: NDVI * 850 (กก./ไร่) / 1000 = ตัน
            yield_ton = (val * 850 * rice_field.area_rai) / 1000
            
            YieldEstimation.objects.create(
                field=rice_field, ndvi_mean=val, estimated_yield_ton=yield_ton
            )
            
            return Response({'ndvi': round(val, 4), 'yield_ton': round(yield_ton, 2)})
        except Exception as e:
            print(f"GEE Error: {e}")
            return Response({'error': 'ระบบดาวเทียมตอบสนองช้า หรือพื้นที่นี้ไม่มีภาพ'}, status=500)

class SaleNotificationViewSet(viewsets.ModelViewSet):
    """จัดการการแจ้งขายผลผลิต"""
    serializer_class = SaleNotificationSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', 'FARMER')
        
        # ✅ แก้ไข: Admin, Miller, Govt เห็น "ทั้งหมด" (ทั้ง OPEN และ CLOSED)
        if user.is_superuser or role in ['MILLER', 'GOVT']:
            return SaleNotification.objects.all().order_by('-created_at')
            
        return SaleNotification.objects.filter(farmer=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)
        
    def perform_update(self, serializer):
        if 'status' in serializer.validated_data and serializer.validated_data['status'] == 'CLOSED':
            # ถ้าเป็น Miller กดซื้อ ให้บันทึกชื่อและเวลา
            if self.request.user.role == 'MILLER':
                serializer.save(buyer=self.request.user, sold_at=datetime.datetime.now())
            else:
                serializer.save()
        else:
            serializer.save()