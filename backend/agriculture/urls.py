from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rice-fields', views.RiceFieldViewSet, basename='ricefield')
router.register(r'sales', views.SaleNotificationViewSet, basename='sales')

urlpatterns = [
    path('dashboard/', views.dashboard_redirect, name='dashboard_router'),
    path('miller/', views.miller_dashboard, name='miller_dashboard'),
    path('govt/', views.govt_dashboard, name='govt_dashboard'),
    path('govt/stats/', views.govt_stats, name='govt_stats'),
    path('history/', views.history_view, name='history'),
    path('api/stats/', views.dashboard_stats, name='api_stats'),
    path('api/', include(router.urls)),
]