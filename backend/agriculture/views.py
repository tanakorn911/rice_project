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

# --- GEE Init ---
try:
    KEY_PATH = os.path.join(settings.BASE_DIR, 'gee-key.json')
    if os.path.exists(KEY_PATH):
        SCOPES = ['https://www.googleapis.com/auth/earthengine']
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
        ee.Initialize(credentials=credentials)
    else:
        ee.Initialize()
except Exception as e:
    print(f"GEE Init Error: {e}")

# --- Views & Dashboard ---
@login_required
def dashboard_redirect(request):
    user = request.user
    view_as = request.GET.get('view')
    if user.is_superuser:
        if view_as == 'miller': return redirect('miller_dashboard')
        if view_as == 'govt': return redirect('govt_dashboard')
        if view_as == 'farmer': return render(request, 'agriculture/dashboard.html')
        return redirect('/admin/')
    
    role = getattr(user, 'role', 'FARMER')
    if role == 'MILLER': return redirect('miller_dashboard')
    elif role == 'GOVT': return redirect('govt_dashboard')
    else: return render(request, 'agriculture/dashboard.html')

@login_required
def miller_dashboard(request): return render(request, 'agriculture/miller_dashboard.html')

@login_required
def govt_dashboard(request): return render(request, 'agriculture/govt_dashboard.html')

# --- API ---
@api_view(['GET'])
@login_required
def dashboard_stats(request):
    estimations = YieldEstimation.objects.filter(field__in=RiceField.objects.all())
    
    total_fields = RiceField.objects.count()
    total_area = RiceField.objects.aggregate(Sum('area_rai'))['area_rai__sum'] or 0
    total_farmers = RiceField.objects.values('owner').distinct().count()
    total_yield = estimations.aggregate(Sum('estimated_yield_ton'))['estimated_yield_ton__sum'] or 0
    
    # คำนวณยอดเงิน
    sold_value = 0
    pending_value = 0
    sales = SaleNotification.objects.all()
    for s in sales:
        val = s.quantity_ton * float(s.price_per_ton)
        if s.status == 'SOLD': sold_value += val
        elif s.status in ['OPEN', 'REQUESTED']: pending_value += val

    variety_data = RiceField.objects.values('variety').annotate(total=Count('variety'))
    variety_dict = dict(RiceField.VARIETY_CHOICES)
    v_labels = [variety_dict.get(item['variety'], item['variety']) for item in variety_data]
    v_data = [item['total'] for item in variety_data]

    return Response({
        'total_fields': total_fields,
        'total_area': round(total_area, 2),
        'total_farmers': total_farmers,
        'total_yield': round(total_yield, 2),
        'sold_value': sold_value,
        'pending_value': pending_value,
        'charts': {'variety': {'labels': v_labels, 'data': v_data}}
    })

class RiceFieldViewSet(viewsets.ModelViewSet):
    serializer_class = RiceFieldSerializer
    def get_queryset(self):
        if not self.request.user.is_authenticated: return RiceField.objects.none()
        user = self.request.user
        role = getattr(user, 'role', 'FARMER')
        if user.is_superuser or role in ['MILLER', 'GOVT']:
            return RiceField.objects.all().order_by('-created_at')
        return RiceField.objects.filter(owner=user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            geom_input = data.get('geometry')
            field_name = data.get('name', 'แปลงนาใหม่').strip() # ตัดช่องว่างหน้าหลัง

            # 1. เช็คว่าชื่อซ้ำไหม (เฉพาะ User คนนี้)
            if RiceField.objects.filter(owner=request.user, name=field_name).exists():
                return Response({'error': f"คุณมีแปลงนาชื่อ '{field_name}' อยู่แล้ว กรุณาตั้งชื่ออื่น"}, status=400)

            if not geom_input: return Response({'error': 'กรุณาวาดแปลงนา'}, status=400)
            if isinstance(geom_input, str): geom_input = json.loads(geom_input)
            poly = GEOSGeometry(json.dumps(geom_input))
            
            centroid = poly.centroid
            if not (99.80 <= centroid.x <= 100.10 and 19.00 <= centroid.y <= 19.35):
                 return Response({'error': 'อยู่นอกเขตพื้นที่ อ.เมืองพะเยา'}, status=400)
            
            area_sqm = poly.transform(32647, clone=True).area
            area_rai = round(area_sqm / 1600, 2)
            
            # บันทึกข้อมูล
            field = RiceField.objects.create(
                owner=request.user, 
                name=field_name,
                boundary=poly, 
                area_rai=area_rai, 
                variety=data.get('variety', 'KDML105')
            )
            return Response({'id': field.id, 'area': area_rai}, status=201)
        except Exception as e: 
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def calculate_yield(self, request, pk=None):
        rice_field = self.get_object()
        try:
            geom_json = json.loads(rice_field.boundary.json)
            ee_geometry = ee.Geometry.Polygon(geom_json['coordinates'])
            
            # --- สูตรคำนวณล่าสุดและแม่นยำที่สุด ---
            # 1. ใช้ภาพย้อนหลัง 1 ปี (30 วัน) เพื่อให้ครอบคลุมฤดูกาลและมีข้อมูลแน่นอน
            # 2. กรองเมฆที่ 80% (เพื่อให้ได้ภาพมากที่สุด)
            # 3. ใช้ .median() หาค่ากลาง (กำจัดเมฆและเงาออกอัตโนมัติ)
            
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=30)
            
            dataset = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(ee_geometry)
                       .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 80)))
            
            if dataset.size().getInfo() == 0:
                return Response({'error': 'เมฆมากเกินไป ไม่สามารถวิเคราะห์ได้ในขณะนี้'}, status=400)

            image = dataset.median()
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            val = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(), 
                geometry=ee_geometry, 
                scale=10, # ความละเอียด 10 เมตร (เร็วและเพียงพอ)
                maxPixels=1e9
            ).get('NDVI').getInfo()
            
            if val is None: return Response({'error': 'พื้นที่เล็กเกินไป'}, status=400)
            
            # --- Logic จำแนกพื้นที่ (Classification) ---
            if val < 0:
                # NDVI ติดลบ คือ น้ำ (Water)
                result_type = 'water'
                yield_ton = 0
                note = "แหล่งน้ำ (Water Body)"
            
            elif 0 <= val < 0.35:
                # NDVI 0 - 0.35 คือ ถนน, ดินโล่ง, สิ่งปลูกสร้าง
                result_type = 'road'
                yield_ton = 0
                note = "ถนน/สิ่งปลูกสร้าง (Urban/Road)"
            
            else:
                # NDVI > 0.35 คือ พืช/แปลงนา (Vegetation)
                result_type = 'rice'
                # สูตรคำนวณผลผลิตปัจจุบัน: (NDVI * 850 * ไร่) / 1000
                yield_ton = (val * 850 * rice_field.area_rai) / 1000
                note = "พื้นที่เกษตร (Rice Field)"
            
            # บันทึกเฉพาะเมื่อเป็นแปลงนาจริง หรือจะบันทึกหมดก็ได้ (ที่นี้บันทึกหมดแต่ yield=0)
            YieldEstimation.objects.create(field=rice_field, ndvi_mean=val, estimated_yield_ton=yield_ton)
            
            return Response({
                'ndvi': round(val, 4), 
                'yield_ton': round(yield_ton, 2), 
                'note': note,
                'result_type': result_type  # ส่ง type กลับไปให้ Frontend เช็ค
            })

        except Exception as e:
            print(f"GEE Error: {e}")
            return Response({'error': 'ระบบดาวเทียมขัดข้องชั่วคราว'}, status=500)

class SaleNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = SaleNotificationSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated: return SaleNotification.objects.none()
        user = self.request.user
        role = getattr(user, 'role', 'FARMER')
        
        if role == 'FARMER':
            return SaleNotification.objects.filter(farmer=user).order_by('-created_at')
        return SaleNotification.objects.filter(Q(status='OPEN') | Q(buyer=user) | Q(status='SOLD')).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)

    @action(detail=True, methods=['post'])
    def request_buy(self, request, pk=None):
        sale = self.get_object()
        if sale.status != 'OPEN': return Response({'error': 'ไม่ว่าง'}, status=400)
        sale.status = 'REQUESTED'
        sale.buyer = request.user
        sale.buyer_contact = request.data.get('contact', '-')
        sale.save()
        return Response({'status': 'requested'})

    @action(detail=True, methods=['post'])
    def approve_sell(self, request, pk=None):
        sale = self.get_object()
        if sale.farmer != request.user: return Response({'error': 'ไม่ใช่เจ้าของ'}, status=403)
        sale.status = 'SOLD'
        sale.sold_at = datetime.datetime.now()
        sale.save()
        return Response({'status': 'sold'})
    
    @action(detail=True, methods=['post'])
    def reject_sell(self, request, pk=None):
        sale = self.get_object()
        if sale.farmer != request.user: return Response({'error': 'ไม่ใช่เจ้าของ'}, status=403)
        sale.status = 'OPEN'
        sale.buyer = None
        sale.buyer_contact = None
        sale.save()
        return Response({'status': 'open'})