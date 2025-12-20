from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import GEOSGeometry
import json

from .models import RiceField, YieldEstimation
from .services.gee_service import get_ndvi_yield


@login_required
def farmer_dashboard(request):
    return render(request, 'farmer_dashboard.html')

# API สำหรับจัดการข้อมูล
class RiceFieldViewSet(viewsets.ModelViewSet):
    queryset = RiceField.objects.all()
    
    def create(self, request):
        """รับข้อมูล GeoJSON จากหน้าเว็บและบันทึก"""
        try:
            data = request.data
            geom_str = json.dumps(data['geometry'])
            poly = GEOSGeometry(geom_str)
            
            # คำนวณไร่แบบง่าย (Area / 1600)
            # หมายเหตุ: เพื่อความแม่นยำควร Transform Projection แต่ใช้ค่าประมาณได้
            area_rai = round(poly.transform(32647, clone=True).area / 1600, 2)

            field = RiceField.objects.create(
                owner=request.user,
                name=data.get('name', 'My Field'),
                boundary=poly,
                area_rai=area_rai,
                district=data.get('district', 'Phayao')
            )
            return Response({'id': field.id, 'area': area_rai})
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """กดปุ่มคำนวณผลผลิต"""
        field = self.get_object()
        geojson = json.loads(field.boundary.json)
        
        result, error = get_ndvi_yield(geojson, field.area_rai)
        
        if error:
            return Response({'error': error}, status=400)
            
        # บันทึกประวัติ
        YieldEstimation.objects.create(
            field=field,
            ndvi_mean=result['ndvi'],
            estimated_yield_ton=result['yield']
        )
        
        return Response(result)