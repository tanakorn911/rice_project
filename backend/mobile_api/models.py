from django.conf import settings
from django.contrib.gis.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_v2')
    full_name = models.CharField(max_length=255)
    national_id = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=32)
    address = models.TextField(blank=True)


class VerificationRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('NOT_SUBMITTED', 'NOT_SUBMITTED'),
        ('PENDING', 'PENDING'),
        ('UNDER_REVIEW', 'UNDER_REVIEW'),
        ('APPROVED', 'APPROVED'),
        ('REJECTED', 'REJECTED'),
        ('RESUBMISSION_REQUIRED', 'RESUBMISSION_REQUIRED'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_requests')
    role = models.CharField(max_length=16)
    document_image = models.ImageField(upload_to='verification/documents/')
    selfie_image = models.ImageField(upload_to='verification/selfies/')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True)
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_verifications')
    reviewed_at = models.DateTimeField(null=True, blank=True)


class DeviceToken(TimeStampedModel):
    PLATFORM_CHOICES = [('IOS', 'IOS'), ('ANDROID', 'ANDROID')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='device_tokens')
    device_platform = models.CharField(max_length=16, choices=PLATFORM_CHOICES)
    token = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)


class FieldRecord(TimeStampedModel):
    STATUS_CHOICES = [('ACTIVE', 'ACTIVE'), ('ARCHIVED', 'ARCHIVED')]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='field_records')
    name = models.CharField(max_length=255)
    location = models.PointField(geography=True)
    area_rai = models.FloatField(default=0)
    boundary_geojson = models.JSONField(null=True, blank=True)
    crop_variety = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='ACTIVE')


class FieldImage(TimeStampedModel):
    field_record = models.ForeignKey(FieldRecord, on_delete=models.CASCADE, related_name='images')
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='field_images')
    original_image = models.ImageField(upload_to='fields/original/')
    processed_image = models.ImageField(upload_to='fields/processed/', null=True, blank=True)
    heatmap_image = models.ImageField(upload_to='fields/photo_heatmap/', null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    captured_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class SatelliteAnalysis(TimeStampedModel):
    field_record = models.ForeignKey(FieldRecord, on_delete=models.CASCADE, related_name='satellite_analyses')
    analysis_date = models.DateTimeField()
    ndvi_value = models.FloatField(null=True, blank=True)
    evi_value = models.FloatField(null=True, blank=True)
    ndwi_value = models.FloatField(null=True, blank=True)
    ndre_value = models.FloatField(null=True, blank=True)
    cloud_percentage = models.FloatField(default=0)
    confidence_score = models.FloatField(default=0)
    heatmap_image = models.ImageField(upload_to='satellite/heatmaps/', null=True, blank=True)
    trend_summary = models.JSONField(default=dict)
    remarks = models.TextField(blank=True)


class PhotoAnalysis(TimeStampedModel):
    field_image = models.OneToOneField(FieldImage, on_delete=models.CASCADE, related_name='photo_analysis')
    quality_score = models.FloatField(default=0)
    color_index = models.FloatField(default=0)
    processed_image = models.ImageField(upload_to='photo_analysis/processed/', null=True, blank=True)
    heatmap_image = models.ImageField(upload_to='photo_analysis/heatmaps/', null=True, blank=True)
    notes = models.TextField(blank=True)


class YieldEstimation(TimeStampedModel):
    field_record = models.ForeignKey(FieldRecord, on_delete=models.CASCADE, related_name='yield_estimations')
    satellite_analysis = models.ForeignKey(SatelliteAnalysis, on_delete=models.SET_NULL, null=True, blank=True)
    estimated_yield_ton = models.FloatField()
    confidence_score = models.FloatField(default=0)
    explanation_note = models.TextField(blank=True)


class SaleListing(TimeStampedModel):
    STATUS_CHOICES = [('DRAFT', 'DRAFT'), ('OPEN', 'OPEN'), ('NEGOTIATING', 'NEGOTIATING'), ('CLOSED', 'CLOSED')]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sale_listings')
    field_record = models.ForeignKey(FieldRecord, on_delete=models.CASCADE, related_name='sale_listings')
    quantity_ton = models.FloatField()
    asking_price_per_ton = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='DRAFT')


class BuyRequest(TimeStampedModel):
    STATUS_CHOICES = [('PENDING', 'PENDING'), ('APPROVED', 'APPROVED'), ('REJECTED', 'REJECTED')]

    sale = models.ForeignKey(SaleListing, on_delete=models.CASCADE, related_name='buy_requests')
    miller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buy_requests')
    offered_price_per_ton = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='PENDING')


class Notification(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications_v2')
    title = models.CharField(max_length=255)
    message = models.TextField()
    deep_link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)


class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preference')
    push_enabled = models.BooleanField(default=True)
    market_updates_enabled = models.BooleanField(default=True)
    analysis_updates_enabled = models.BooleanField(default=True)
    verification_updates_enabled = models.BooleanField(default=True)


class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=128)
    target_type = models.CharField(max_length=64)
    target_id = models.CharField(max_length=64)
    detail = models.JSONField(default=dict)
