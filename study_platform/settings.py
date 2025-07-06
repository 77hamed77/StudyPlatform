from pathlib import Path
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

# تحميل المتغيرات البيئية مرة واحدة
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- إعدادات الأمان الأساسية ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'CHANGE_THIS_SECRET_KEY')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
KOYEB_PUBLIC_HOST = os.environ.get('DJANGO_ALLOWED_HOST')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
if KOYEB_PUBLIC_HOST:
    ALLOWED_HOSTS.append(KOYEB_PUBLIC_HOST)
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

CSRF_TRUSTED_ORIGINS = []
if not DEBUG:
    if RENDER_EXTERNAL_HOSTNAME:
        CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
    if KOYEB_PUBLIC_HOST:
        CSRF_TRUSTED_ORIGINS.append(f'https://{KOYEB_PUBLIC_HOST}')
elif DEBUG:
    CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])

X_FRAME_OPTIONS = 'DENY'  # تغيير إلى DENY للأمان

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'storages',
    'achievements.apps.AchievementsConfig',
    'chat_assistant.apps.ChatAssistantConfig',
    'core.apps.CoreConfig',
    'exam_prep.apps.ExamPrepConfig',
    'files_manager.apps.FilesManagerConfig',
    'news.apps.NewsConfig',
    'notes.apps.NotesConfig',
    'tasks.apps.TasksConfig',
    'prayer_times.apps.PrayerTimesConfig',  # تأكيد وجوده
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

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

# إعدادات قاعدة البيانات
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
    DATABASES['default'].update({
        'OPTIONS': {'sslmode': 'require'},
        'CONN_MAX_AGE': 600,
    })
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("WARNING: DATABASE_URL environment variable not set. Using SQLite for local development.")

if 'default' not in DATABASES or 'ENGINE' not in DATABASES['default']:
    raise ImproperlyConfigured("DATABASE_URL environment variable is not set or improperly configured.")

# إعدادات تخزين S3 (Supabase)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-central-1')
AWS_S3_SIGNATURE_VERSION = os.environ.get('AWS_S3_SIGNATURE_VERSION', 's3v4')
AWS_S3_FILE_OVERWRITE = os.environ.get('AWS_S3_FILE_OVERWRITE', 'False').lower() == 'true'
AWS_DEFAULT_ACL = os.environ.get('AWS_DEFAULT_ACL', 'public-read')
AWS_QUERYSTRING_AUTH = os.environ.get('AWS_QUERYSTRING_AUTH', 'False').lower() == 'true'
AWS_S3_USE_SSL = os.environ.get('AWS_S3_USE_SSL', 'True').lower() == 'true'
AWS_LOCATION = os.environ.get('AWS_LOCATION', '')
AWS_QUERYSTRING_EXPIRE = int(os.environ.get('AWS_QUERYSTRING_EXPIRE', 3600))

AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

if AWS_S3_ENDPOINT_URL and AWS_STORAGE_BUCKET_NAME:
    _supabase_base_url = AWS_S3_ENDPOINT_URL.replace('/s3', '/object/public/')
    _bucket_url_part = f"{_supabase_base_url}{AWS_STORAGE_BUCKET_NAME}/"
    if AWS_LOCATION:
        MEDIA_URL = f"{_bucket_url_part}{AWS_LOCATION}/"
    else:
        MEDIA_URL = _bucket_url_part
    print(f"INFO: Using Supabase Storage. MEDIA_URL set to: {MEDIA_URL}")
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    print("WARNING: Supabase Storage environment variables not fully set. Using local file storage for media.")

if not DEBUG and DEFAULT_FILE_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage':
    required_s3_vars = [AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_ENDPOINT_URL]
    if not all(required_s3_vars):
        raise ImproperlyConfigured("Missing one or more AWS S3 environment variables required for Supabase Storage in production!")

# إعدادات Celery
REDIS_URL = os.environ.get('REDIS_URL', 'redis://red-d1l4fh15pdvs73bgm3cg.render.com:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Riyadh' # <--- تم تغيير هذا بالفعل في المحادثة السابقة

# إعدادات الثابتة
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_collected'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# إعدادات الأمان الإضافية
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Damascus' # <--- هذا تم تغييره بالفعل
USE_I18N = True
USE_TZ = True
LANGUAGES = [('en', _('English')), ('ar', _('Arabic'))]
LOCALE_PATHS = [BASE_DIR / 'locale']

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'login'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# إعدادات السجل (Logging)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': True},
        '': {'handlers': ['console'], 'level': 'INFO', 'propagate': True},
    },
}

if not DEBUG:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        logger.info("Database connection successful!")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

# --- إعدادات أوقات الصلاة (جديد) ---
# إحداثيات المدينة الافتراضية (دمشق، سوريا)
DEFAULT_PRAYER_TIMES_LATITUDE = os.environ.get('DEFAULT_PRAYER_TIMES_LATITUDE', '33.5104') # خط عرض دمشق
DEFAULT_PRAYER_TIMES_LONGITUDE = os.environ.get('DEFAULT_PRAYER_TIMES_LONGITUDE', '36.2784') # خط طول دمشق
DEFAULT_PRAYER_TIMES_METHOD = os.environ.get('DEFAULT_PRAYER_TIMES_METHOD', '4') # 4 = Umm Al-Qura University, Makkah
# ALADHAN_API_BASE_URL = os.environ.get('ALADHAN_API_BASE_URL', 'http://api.aladhan.com/v1') # هذا موجود بالفعل
