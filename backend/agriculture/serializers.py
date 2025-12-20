from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import RiceField, YieldEstimation, SaleNotification

class RiceFieldSerializer(serializers.ModelSerializer):
    variety_display = serializers.CharField(source='get_variety_display', read_only=True)
    class Meta:
        model = RiceField
        fields = '__all__'

class YieldEstimationSerializer(serializers.ModelSerializer):
    class Meta:
        model = YieldEstimation
        fields = '__all__'

class SaleNotificationSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.username', read_only=True)
    field_name = serializers.CharField(source='rice_field.name', read_only=True)
    variety_display = serializers.CharField(source='rice_field.get_variety_display', read_only=True)
    field_location = serializers.SerializerMethodField()

    class Meta:
        model = SaleNotification
        fields = ['id', 'farmer_name', 'rice_field', 'field_name', 'field_location', 'variety_display', 
                  'quantity_ton', 'price_per_ton', 'phone', 'status', 'created_at']

    def get_field_location(self, obj):
        if obj.rice_field and obj.rice_field.boundary:
            return obj.rice_field.boundary.json
        return None