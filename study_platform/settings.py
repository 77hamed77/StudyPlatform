# study_platform/settings.py
from pathlib import Path
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured # استيراد ImproperlyConfigured

# NEW: تحميل متغيرات البيئة من ملف .env للاختبار المحلي
# تأكد من تثبيت python-dotenv: pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
# ---------------------------------------------------------------------------

from django.utils.translation import gettext_lazy as _ # للترجمة (جيد إبقاؤه)

# مسارات البناء داخل المشروع
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# اقرأ SECRET_KEY من متغير بيئة، مع قيمة افتراضية للتطوير المحلي فقط
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    '0nPNq5cbMmsK2MQRSW3aO27GB-pMw5pe8m5d7hLcEVNbRriYx-nG4-sQZPpy8rU-kwE' # !!! هام: قم بتغيير هذا لمفتاح سري فريد إذا كنت ستستخدمه حتى في الإنتاج الصغير !!!
)

# SECURITY WARNING: don't run with debug turned on in production!
# يجب أن تكون False في الإنتاج!
DEBUG_VALUE = os.environ.get('DJANGO_DEBUG', 'False')
DEBUG = DEBUG_VALUE.lower() in ('true', '1', 't')


ALLOWED_HOSTS = []
# اقرأ النطاق من متغير بيئة DJANGO_ALLOWED_HOST
KOYEB_PUBLIC_HOST = os.environ.get('DJANGO_ALLOWED_HOST')
if KOYEB_PUBLIC_HOST:
    ALLOWED_HOSTS.append(KOYEB_PUBLIC_HOST)

# أضف localhost و 127.0.0.1 للتطوير المحلي فقط
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # تطبيقاتك الخاصة
    'core.apps.CoreConfig',
    'files_manager.apps.FilesManagerConfig',
    'news.apps.NewsConfig',
    'tasks.apps.TasksConfig',
    'notes.apps.NotesConfig',
    'exam_prep.apps.ExamPrepConfig',
    'achievements.apps.AchievementsConfig',
    # تطبيقات طرف ثالث
    'crispy_forms',
    'crispy_bootstrap5',
]

# Cloudinary Storage for media files (Uploads)
INSTALLED_APPS += [
    'cloudinary',
    'cloudinary_storage',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_DEFAULT_TEMPLATE_PACK = "bootstrap5"

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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.common_context',
            ],
        },
    },
]
WSGI_APPLICATION = 'study_platform.wsgi.application'


# Database
# تم إزالة DEFAULT_DATABASE_URL كقيمة افتراضية لـ dj_database_url.config
# مما يجبره على استخدام DATABASE_URL من متغيرات البيئة.
# إذا لم يتم تعيين DATABASE_URL بشكل صحيح، فسيتم رفع ImproperlyConfigured.
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'), # لا يوجد fallback على SQLite هنا
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# هذا الشرط سيجعل Django يفشل مبكراً إذا لم يتم تكوين قاعدة البيانات بشكل صحيح
# مما يوفر رسالة خطأ أوضح في سجلات البناء/التشغيل
if 'default' not in DATABASES or 'ENGINE' not in DATABASES['default']:
    raise ImproperlyConfigured("DATABASE_URL environment variable is not set or improperly configured. Please provide a valid PostgreSQL URL.")


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'

USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_collected')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Media files (Uploaded by users)
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# Authentication settings
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'
LOGIN_URL = 'login'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF_TRUSTED_ORIGINS (مهم جداً في الإنتاج)
CSRF_TRUSTED_ORIGINS = []
if not DEBUG and KOYEB_PUBLIC_HOST:
     # تأكد من أنها HTTPS للنطاق العام لـ Koyeb
    CSRF_TRUSTED_ORIGINS = [f'https://{KOYEB_PUBLIC_HOST}']
elif DEBUG:
    # للتطوير المحلي
    CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])


# لإجبار الاتصالات على HTTPS في الإنتاج (إذا كان DEBUG=False)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# إعدادات التسجيل (LOGGING) - سيتم توجيه السجلات إلى الـ console (سجلات Koyeb)
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
            'level': 'INFO', # يمكنك تغييرها إلى 'DEBUG' إذا كنت تريد المزيد من التفاصيل
            'propagate': True,
        },
        '': { # لـ loggers التطبيق الأخرى
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}