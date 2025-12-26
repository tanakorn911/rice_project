from rest_framework import serializers
from .models import RiceField, YieldEstimation, SaleNotification

class RiceFieldSerializer(serializers.ModelSerializer):
    variety_display = serializers.CharField(source='get_variety_display', read_only=True)
    boundary = serializers.SerializerMethodField()
    latest_yield = serializers.SerializerMethodField()

    class Meta:
        model = RiceField
        fields = '__all__'

    def get_boundary(self, obj):
        if obj.boundary: return obj.boundary.json
        return None

    def get_latest_yield(self, obj):
        estimation = obj.yieldestimation_set.order_by('-created_at').first()
        if estimation:
            return {'ndvi': estimation.ndvi_mean, 'yield': estimation.estimated_yield_ton}
        return None

class YieldEstimationSerializer(serializers.ModelSerializer):
    class Meta:
        model = YieldEstimation
        fields = '__all__'

class SaleNotificationSerializer(serializers.ModelSerializer):
    # --- ข้อมูลเกษตรกร (Seller) ---
    farmer_name = serializers.CharField(source='farmer.get_full_name', read_only=True)
    farmer_phone = serializers.CharField(source='farmer.phone', read_only=True)
    farmer_line = serializers.CharField(source='farmer.line_id', read_only=True)
    farmer_address = serializers.CharField(source='farmer.address', read_only=True)
    farmer_bio = serializers.CharField(source='farmer.about_me', read_only=True)
    
    # --- ข้อมูลแปลงนา ---
    field_name = serializers.CharField(source='rice_field.name', read_only=True)
    field_area = serializers.FloatField(source='rice_field.area_rai', read_only=True)
    variety_display = serializers.CharField(source='rice_field.get_variety_display', read_only=True)
    field_location = serializers.SerializerMethodField()
    
    # +++ เพิ่มพิกัดสำหรับนำทาง +++
    field_lat = serializers.SerializerMethodField()
    field_lng = serializers.SerializerMethodField()

    # --- ข้อมูลผู้ซื้อ (Buyer/Miller) ---
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    buyer_phone = serializers.CharField(source='buyer.phone', read_only=True)
    buyer_line = serializers.CharField(source='buyer.line_id', read_only=True)
    buyer_address = serializers.CharField(source='buyer.address', read_only=True)
    buyer_bio = serializers.CharField(source='buyer.about_me', read_only=True)

    class Meta:
        model = SaleNotification
        fields = [
            'id', 'status', 'created_at', 'sold_at', 'quantity_ton', 'price_per_ton', 'negotiated_price',
            'rice_field', 'field_name', 'field_area', 'field_location', 'field_lat', 'field_lng', 'variety_display',
            'farmer_name', 'farmer_phone', 'farmer_line', 'farmer_address', 'farmer_bio', 'phone',
            'buyer', 'buyer_name', 'buyer_phone', 'buyer_contact', 'buyer_line', 'buyer_address', 'buyer_bio'
        ]

    def get_field_location(self, obj):
        if obj.rice_field and obj.rice_field.boundary:
            return obj.rice_field.boundary.json
        return None

    # +++ ฟังก์ชันหาจุดกึ่งกลางแปลงนา +++
    def get_field_lat(self, obj):
        if obj.rice_field and obj.rice_field.boundary:
            return obj.rice_field.boundary.centroid.y
        return None

    def get_field_lng(self, obj):
        if obj.rice_field and obj.rice_field.boundary:
            return obj.rice_field.boundary.centroid.x
        return None