from django.contrib.auth import login, logout
from django.utils import timezone
from django.core import signing
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

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
from .serializers import (
    LoginSerializer,
    VerificationRequestSerializer,
    FieldRecordSerializer,
    FieldImageSerializer,
    SatelliteAnalysisSerializer,
    PhotoAnalysisSerializer,
    YieldEstimationSerializer,
    SaleListingSerializer,
    BuyRequestSerializer,
    NotificationSerializer,
    DeviceTokenSerializer,
    NotificationPreferenceSerializer,
)
from .services.satellite import run_sentinel_analysis
from .services.photo import run_photo_analysis


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    login(request, user)
    access_token = signing.dumps({'uid': user.id, 'type': 'access'})
    refresh_token = signing.dumps({'uid': user.id, 'type': 'refresh'})
    return Response({'access': access_token, 'refresh': refresh_token, 'role': user.role})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    logout(request)
    return Response({'detail': 'logged out'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_me(request):
    return Response({'id': request.user.id, 'username': request.user.username, 'role': request.user.role})


class VerificationViewSet(viewsets.ModelViewSet):
    queryset = VerificationRequest.objects.all().order_by('-created_at')
    serializer_class = VerificationRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role in ['ADMIN', 'GOVT']:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='PENDING')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = 'APPROVED'
        obj.reviewed_by = request.user
        obj.reviewed_at = timezone.now()
        obj.save()
        return Response({'status': obj.status})


class FieldRecordViewSet(viewsets.ModelViewSet):
    serializer_class = FieldRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = FieldRecord.objects.all().order_by('-created_at')
        if self.request.user.role in ['ADMIN', 'GOVT']:
            return qs
        return qs.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def run_satellite_analysis(self, request, pk=None):
        field = self.get_object()
        summary = run_sentinel_analysis(field)
        analysis = SatelliteAnalysis.objects.create(
            field_record=field,
            analysis_date=timezone.now(),
            ndvi_value=summary.ndvi,
            evi_value=summary.evi,
            ndwi_value=summary.ndwi,
            ndre_value=summary.ndre,
            confidence_score=summary.confidence,
            remarks=summary.notes,
        )
        return Response(SatelliteAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def satellite_analysis(self, request, pk=None):
        field = self.get_object()
        rows = field.satellite_analyses.all().order_by('-analysis_date')
        return Response(SatelliteAnalysisSerializer(rows, many=True).data)


class FieldImageViewSet(viewsets.ModelViewSet):
    serializer_class = FieldImageSerializer
    permission_classes = [IsAuthenticated]
    queryset = FieldImage.objects.all().order_by('-uploaded_at')

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

    @action(detail=True, methods=['post'])
    def run_photo_analysis(self, request, pk=None):
        image = self.get_object()
        summary = run_photo_analysis(image)
        analysis, _ = PhotoAnalysis.objects.update_or_create(
            field_image=image,
            defaults={
                'quality_score': summary.quality_score,
                'color_index': summary.color_index,
                'notes': summary.notes,
            },
        )
        return Response(PhotoAnalysisSerializer(analysis).data)


class SaleListingViewSet(viewsets.ModelViewSet):
    serializer_class = SaleListingSerializer
    permission_classes = [IsAuthenticated]
    queryset = SaleListing.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=True, methods=['post'])
    def request_buy(self, request, pk=None):
        sale = self.get_object()
        serializer = BuyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        buy_request = serializer.save(sale=sale, miller=request.user)
        sale.status = 'NEGOTIATING'
        sale.save(update_fields=['status'])
        return Response(BuyRequestSerializer(buy_request).data, status=status.HTTP_201_CREATED)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        row = self.get_object()
        row.is_read = True
        row.save(update_fields=['is_read'])
        return Response({'is_read': True})


class DeviceTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
