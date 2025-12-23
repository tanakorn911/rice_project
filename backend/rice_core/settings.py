import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# SECRET_KEY = 'django-insecure-change-me-please'
# DEBUG = True
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-me-please"
)

DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',       # <--- ต้องมี
    'rest_framework',
    'users',
    'agriculture',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # <--- สำคัญสำหรับ Form
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rice_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # <--- ชี้ไปที่โฟลเดอร์ templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rice_core.wsgi.application'

# Database เชื่อมกับ Docker
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': 'rice_db',
#         'USER': 'postgres',
#         'PASSWORD': 'password',
#         'HOST': 'db', # ชื่อ Service ใน Docker compose
#         'PORT': '5432',
#     }
# }
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = 'users.User'
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# เมื่อ Login สำเร็จ ให้เด้งไปที่ URL name ที่ชื่อว่า 'dashboard'
LOGIN_REDIRECT_URL = 'dashboard_router'

# (แนะนำ) เมื่อ Logout สำเร็จ ให้กลับมาหน้า Login
LOGOUT_REDIRECT_URL = 'login'
LOGOUT_ON_GET = True

CSRF_TRUSTED_ORIGINS = [
    "https://riceproject-production.up.railway.app",
    
]
