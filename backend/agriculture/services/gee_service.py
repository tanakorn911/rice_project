import ee
import os
import datetime
from google.oauth2 import service_account

def initialize_gee():
    """เชื่อมต่อ GEE ด้วย Key File"""
    try:
        key_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'gee-key.json')
        if not os.path.exists(key_path):
            print(f"Warning: Key file not found at {key_path}")
            return

        credentials = service_account.Credentials.from_service_account_file(key_path)
        scoped_credentials = credentials.with_scopes(
            ['https://www.googleapis.com/auth/earthengine']
        )
        ee.Initialize(credentials=scoped_credentials)
        print("GEE Initialized Successfully!")
    except Exception as e:
        print(f"GEE Error: {e}")

# เรียกใช้ทันทีเมื่อ import
initialize_gee()

def get_ndvi_yield(geojson_geom, area_rai):
    """คำนวณ NDVI และผลผลิต"""
    try:
        # 1. แปลง Geometry
        region = ee.Geometry.Polygon(geojson_geom['coordinates'])

        # 2. ช่วงเวลา (ย้อนหลัง 1 เดือน)
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=30)

        # 3. ดึงภาพ Sentinel-2 (Level 2A)
        s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(region) \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .sort('CLOUDY_PIXEL_PERCENTAGE')

        count = s2.size().getInfo()
        if count == 0:
            return None, "ไม่พบภาพดาวเทียมที่ปลอดเมฆในช่วงนี้"

        image = s2.first()

        # 4. คำนวณ NDVI
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # 5. หาค่าเฉลี่ยในแปลงนา
        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=10,
            maxPixels=1e9
        )
        
        ndvi_val = stats.get('NDVI').getInfo()
        
        if ndvi_val is None:
            ndvi_val = 0

        # 6. สูตรคำนวณผลผลิต (ตัวอย่าง)
        # ผลผลิต (ตัน) = ไร่ * NDVI * 0.5
        predicted_yield = area_rai * max(0, ndvi_val) * 0.5
        
        return {
            'ndvi': round(ndvi_val, 3),
            'yield': round(predicted_yield, 2)
        }, None

    except Exception as e:
        return None, str(e)