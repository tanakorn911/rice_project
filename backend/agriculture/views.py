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
from django.views.decorators.csrf import csrf_exempt # <--- สำคัญสำหรับ API
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
    # 1. ข้อมูลพื้นฐานแปลงนา
    all_fields = RiceField.objects.all()
    total_fields = all_fields.count()
    total_area = all_fields.aggregate(Sum('area_rai'))['area_rai__sum'] or 0
    total_farmers = all_fields.values('owner').distinct().count()
    
    # 2. คำนวณยอดเงิน และ ปริมาณผลผลิต (จากรายการขายจริง ไม่ใช่ดาวเทียม)
    sales = SaleNotification.objects.all()
    
    total_yield = 0      # เก็บปริมาณตันรวม
    sold_value = 0       # มูลค่าขายแล้ว
    pending_value = 0    # มูลค่ารอขาย

    for s in sales:
        val = s.quantity_ton * float(s.price_per_ton)
        
        if s.status == 'SOLD': 
            sold_value += val
        elif s.status in ['OPEN', 'REQUESTED']: 
            pending_value += val
            
        # นับรวมทุกสถานะที่เป็น active supply
        if s.status in ['SOLD', 'OPEN', 'REQUESTED']:
            total_yield += s.quantity_ton

    # 3. เตรียมข้อมูลกราฟ
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
            field_name = data.get('name', 'แปลงนาใหม่').strip()

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
            
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=60) 
            
            def mask_s2_scl(image):
                scl = image.select('SCL')
                mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
                return image.updateMask(mask).divide(10000)

            dataset = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(ee_geometry)
                       .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 70))
                       .map(mask_s2_scl))

            if dataset.size().getInfo() == 0:
                return Response({'error': 'ไม่พบภาพดาวเทียมที่ไม่มีเมฆในช่วงนี้'}, status=400)

            # ดึงค่าเมฆเฉลี่ยจากชุดข้อมูล
            cloud_score = dataset.aggregate_mean('CLOUDY_PIXEL_PERCENTAGE').getInfo() or 0
            
            image = dataset.median()
            vis_params = {'min': 0.0, 'max': 0.3, 'bands': ['B4', 'B3', 'B2'], 'gamma': 1.3}
            map_id = image.getMapId(vis_params)
            tile_url = map_id['tile_fetcher'].url_format

            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            ndbi = image.normalizedDifference(['B11', 'B8']).rename('NDBI')

            combined = ndvi.addBands(ndbi)
            stats = combined.reduceRegion(
                reducer=ee.Reducer.mean(), 
                geometry=ee_geometry, 
                scale=10, 
                maxPixels=1e9
            ).getInfo()
            
            val_ndvi = stats.get('NDVI') or 0
            val_ndbi = stats.get('NDBI') or 0
            
            yield_ton = 0
            revenue = 0
            result_type = 'rice'
            note = "นาข้าวสมบูรณ์"

            if val_ndvi < 0:
                result_type = 'water'
                note = "แหล่งน้ำ"
            elif val_ndbi > 0.1:
                result_type = 'building'
                note = "อาคาร/สิ่งปลูกสร้าง"
            elif val_ndvi < 0.35:
                result_type = 'road'
                note = "ถนน/ดินโล่ง"
            else:
                yield_ton = (val_ndvi * 850 * rice_field.area_rai) / 1000
                est_price = 14000 if rice_field.variety == 'KDML105' else 12000
                revenue = yield_ton * est_price
            
            # เก็บลง Database และดึงวันที่วิเคราะห์จริงออกมา
            estimation = YieldEstimation.objects.create(
                field=rice_field, 
                ndvi_mean=val_ndvi, 
                estimated_yield_ton=yield_ton
            )
            
            # ส่งข้อมูลกลับให้ครบตามที่หน้าบ้านต้องการ
            return Response({
                'ndvi': round(val_ndvi, 3),
                'ndbi': round(val_ndbi, 3),
                'yield_ton': round(yield_ton, 2), 
                'revenue': round(revenue, 2),
                'note': note,
                'result_type': result_type,
                'area': rice_field.area_rai,
                'satellite_image': tile_url,
                'cloud_cover': round(cloud_score, 1),
                'created_at': estimation.created_at.isoformat() 
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)

class SaleNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = SaleNotificationSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated: return SaleNotification.objects.none()
        user = self.request.user
        role = getattr(user, 'role', 'FARMER')
        
        if user.is_superuser or role == 'GOVT':
            return SaleNotification.objects.all().order_by('-created_at')
        
        if role == 'FARMER':
            return SaleNotification.objects.filter(farmer=user).order_by('-created_at')
        return SaleNotification.objects.filter(Q(status='OPEN') | Q(buyer=user) | Q(status='SOLD')).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)

    @action(detail=True, methods=['post'])
    def request_buy(self, request, pk=None):
        sale = self.get_object()
        if sale.status != 'OPEN': 
            return Response({'error': 'รายการนี้ไม่ว่างหรือมีการขอซื้อแล้ว'}, status=400)
        
        sale.status = 'REQUESTED'
        sale.buyer = request.user
        sale.buyer_contact = request.data.get('contact', request.user.phone or '-')
        sale.save()
        return Response({'status': 'requested', 'msg': 'ส่งคำขอซื้อเรียบร้อย รอชาวนายืนยัน'})

    @action(detail=True, methods=['post'])
    def approve_sell(self, request, pk=None):
        sale = self.get_object()
        if sale.farmer != request.user: 
            return Response({'error': 'คุณไม่ใช่เจ้าของรายการนี้'}, status=403)
        
        if sale.status != 'REQUESTED':
            return Response({'error': 'สถานะรายการไม่ถูกต้อง'}, status=400)

        sale.status = 'SOLD'
        sale.sold_at = datetime.datetime.now()
        sale.save()
        return Response({'status': 'sold', 'msg': 'ยืนยันการขายสำเร็จ'})
    
    @action(detail=True, methods=['post'])
    def reject_sell(self, request, pk=None):
        sale = self.get_object()
        if sale.farmer != request.user: 
            return Response({'error': 'คุณไม่ใช่เจ้าของรายการนี้'}, status=403)
        
        sale.status = 'OPEN'
        sale.buyer = None
        sale.buyer_contact = None
        sale.save()
        return Response({'status': 'open', 'msg': 'ปฏิเสธคำขอแล้ว รายการกลับสู่ตลาด'})
    
@login_required
def history_view(request):
    user = request.user
    role = getattr(user, 'role', 'FARMER')
    
    if role == 'FARMER':
        transactions = SaleNotification.objects.filter(farmer=user, status='SOLD').order_by('-sold_at')
    elif role == 'MILLER':
        transactions = SaleNotification.objects.filter(buyer=user, status='SOLD').order_by('-sold_at')
    elif role == 'GOVT':
        transactions = SaleNotification.objects.filter(status='SOLD').order_by('-sold_at')
    else:
        transactions = [] 

    return render(request, 'agriculture/history.html', {'transactions': transactions, 'role': role})