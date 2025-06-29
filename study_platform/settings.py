from pathlib import Path
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

# تحميل متغيرات البيئة من ملف .env للاختبار المحلي (إذا كان موجوداً)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- إعدادات الأمان الأساسية ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'CHANGE_THIS_SECRET_KEY')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS = []
KOYEB_PUBLIC_HOST = os.environ.get('DJANGO_ALLOWED_HOST')
if KOYEB_PUBLIC_HOST:
    ALLOWED_HOSTS.append(KOYEB_PUBLIC_HOST)
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

CSRF_TRUSTED_ORIGINS = []
if not DEBUG and KOYEB_PUBLIC_HOST:
    CSRF_TRUSTED_ORIGINS.append(f'https://{KOYEB_PUBLIC_HOST}')
elif DEBUG:
    CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])

X_FRAME_OPTIONS = 'ALLOWALL'

# --- تعريف التطبيقات ---
INSTALLED_APPS = [
    # تطبيقات Django الأساسية
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    # تطبيقات الطرف الثالث
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',

    # تطبيقاتك الخاصة
    'achievements.apps.AchievementsConfig',
    'core.apps.CoreConfig',
    'exam_prep.apps.ExamPrepConfig',
    'files_manager.apps.FilesManagerConfig',
    'news.apps.NewsConfig',
    'notes.apps.NotesConfig',
    'tasks.apps.TasksConfig',

    # دعم التخزين عبر Supabase/S3
    'storages',
]

# --- إعدادات Crispy Forms ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'study_platform.urls'

# --- إعدادات القوالب ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'study_platform.wsgi.application'

# --- إعدادات قاعدة البيانات ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("WARNING: DATABASE_URL environment variable not set. Using SQLite for local development.")

if 'default' not in DATABASES or 'ENGINE' not in DATABASES['default']:
    raise ImproperlyConfigured("DATABASE_URL environment variable is not set or improperly configured. Please provide a valid PostgreSQL URL or ensure local SQLite setup is correct.")

# --- إعدادات التخزين عبر Supabase/S3 (فقط للملفات الجديدة) ---
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-central-1')
AWS_S3_SIGNATURE_VERSION = os.environ.get('AWS_S3_SIGNATURE_VERSION', 's3v4')
AWS_S3_FILE_OVERWRITE = os.environ.get('AWS_S3_FILE_OVERWRITE', 'False') == 'True'
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = os.environ.get('AWS_QUERYSTRING_AUTH', 'False') == 'True'
AWS_S3_USE_SSL = os.environ.get('AWS_S3_USE_SSL', 'True') == 'True'  # أضفنا هذا السطر

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
    'ACL': 'public-read',
}

if not os.environ.get('DJANGO_COLLECTSTATIC'):
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_ENDPOINT_URL]):
        raise ImproperlyConfigured("Missing one or more AWS S3 environment variables!")
        
# --- الملفات الثابتة (Static Files) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_collected'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- ملفات الوسائط (Media Files - المرفوعة من المستخدمين) ---
# تم تعطيل MEDIA_ROOT و MEDIA_URL لأن التخزين الآن على Supabase/S3 فقط

# --- مصادقة كلمات المرور ---
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# --- الترجمة والعولمة ---
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'

USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# --- إعدادات المصادقة ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}