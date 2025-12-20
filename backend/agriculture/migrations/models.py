from django.contrib.gis.db import models
from django.conf import settings

class RiceField(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    boundary = models.PolygonField(srid=4326) # เก็บพิกัดภูมิศาสตร์
    area_rai = models.FloatField(default=0.0)
    district = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class YieldEstimation(models.Model):
    field = models.ForeignKey(RiceField, on_delete=models.CASCADE)
    date_calculated = models.DateTimeField(auto_now_add=True)
    ndvi_mean = models.FloatField()
    estimated_yield_ton = models.FloatField()