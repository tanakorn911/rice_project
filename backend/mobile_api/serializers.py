from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import (
    VerificationRequest,
    FieldRecord,
    FieldImage,
    SatelliteAnalysis,
    PhotoAnalysis,
    YieldEstimation,
    SaleListing,
    BuyRequest,
    Notification,
    DeviceToken,
    NotificationPreference,
)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        attrs['user'] = user
        return attrs


class VerificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = '__all__'
        read_only_fields = ('reviewed_by', 'reviewed_at')


class FieldRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldRecord
        fields = '__all__'
        read_only_fields = ('owner',)


class FieldImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldImage
        fields = '__all__'
        read_only_fields = ('uploader',)


class SatelliteAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SatelliteAnalysis
        fields = '__all__'


class PhotoAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoAnalysis
        fields = '__all__'


class YieldEstimationSerializer(serializers.ModelSerializer):
    class Meta:
        model = YieldEstimation
        fields = '__all__'


class SaleListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleListing
        fields = '__all__'
        read_only_fields = ('seller',)


class BuyRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyRequest
        fields = '__all__'
        read_only_fields = ('miller',)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = '__all__'
        read_only_fields = ('user',)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ('user',)
