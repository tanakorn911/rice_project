from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    auth_login,
    auth_logout,
    auth_me,
    VerificationViewSet,
    FieldRecordViewSet,
    FieldImageViewSet,
    SaleListingViewSet,
    NotificationViewSet,
    DeviceTokenViewSet,
    NotificationPreferenceViewSet,
)

router = DefaultRouter()
router.register('verification', VerificationViewSet, basename='verification')
router.register('field-records', FieldRecordViewSet, basename='field-records')
router.register('field-images', FieldImageViewSet, basename='field-images')
router.register('sales', SaleListingViewSet, basename='sales')
router.register('notifications', NotificationViewSet, basename='notifications')
router.register('device-tokens', DeviceTokenViewSet, basename='device-tokens')
router.register('notification-preferences', NotificationPreferenceViewSet, basename='notification-preferences')

urlpatterns = [
    path('auth/login/', auth_login),
    path('auth/logout/', auth_logout),
    path('auth/me/', auth_me),
    path('', include(router.urls)),
]
