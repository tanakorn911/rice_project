import os
from django.core.wsgi import get_wsgi_application

# ต้องชี้ไปที่ settings ของเรา
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rice_core.settings')

application = get_wsgi_application()