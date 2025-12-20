from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'fields', views.RiceFieldViewSet, basename='ricefield')

urlpatterns = [
    path('dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('api/', include(router.urls)),
]