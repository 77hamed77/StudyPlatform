import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', '0nPNq5cbMmsK2MQRSW3aO27GB-pMw5pe8m5d7hLcEVNbRriYx-nG4-sQZPpy8rU-kwE')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # تطبيقات الطرف الثالث
    'crispy_forms',
    'crispy_bootstrap5', # تأكد من أنك تستخدم هذا أو crispy_bootstrap4 بناءً على البوتستراب لديك
    'widget_tweaks', # لإدارة الـ widgets في القوالب
    # 'cloudinary', # <--- تم إزالة هذا
    # 'cloudinary_storage', # <--- تم إزالة هذا
    
    # تطبيقاتي
    'accounts',
    'files_manager',
    'homepage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # لتخديم الملفات الثابتة في الإنتاج
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # لتفعيل الترجمة
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
        'DIRS': [BASE_DIR / 'templates'], # مجلد القوالب الرئيسي للمشروع
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media', # مهم للوصول إلى MEDIA_URL في القوالب
            ],
        },
    }
]

WSGI_APPLICATION = 'study_platform.wsgi.application'


# Database
# إذا كان متغير البيئة DATABASE_URL موجوداً، استخدمه (للنشر مثلاً)
# وإلا، استخدم SQLite لقاعدة البيانات المحلية للتطوير
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # إعدادات SQLite للتطوير المحلي إذا لم يتم تحديد DATABASE_URL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("WARNING: DATABASE_URL environment variable not set. Using SQLite for local development.")


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ar' # تعيين اللغة الافتراضية إلى العربية

TIME_ZONE = 'UTC'

USE_I18N = True # تفعيل الترجمة
USE_L10N = True # تفعيل التوطين (الخاص بالتواريخ والأرقام)
USE_TZ = True # تفعيل دعم المناطق الزمنية

# قائمة اللغات المدعومة
LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale', # مسار ملفات الترجمة
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static', # مجلد الملفات الثابتة في جذر المشروع
]
STATIC_ROOT = BASE_DIR / 'staticfiles' # المجلد الذي سيجمع فيه collectstatic الملفات

# Media files (user uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # المجلد الذي ستُخزن فيه الملفات المرفوعة

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'homepage:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Cloudinary configuration (REMOVE THESE)
# CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
# CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
# CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
#
# DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage' # <--- تم إزالة هذا

# Configure Django's built-in file storage for media files
# This line is IMPORTANT for local storage if not using Cloudinary or other cloud storage
# If DEFAULT_FILE_STORAGE is not defined, Django defaults to FileSystemStorage (local)
# So, we simply ensure it's not pointing to Cloudinary.
# If you wanted to explicitly set it to local storage, you would use:
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage' 
# However, this is the default, so removing the Cloudinary line is often enough.


# Set X_FRAME_OPTIONS to ALLOWALL for iframe embedding
X_FRAME_OPTIONS = 'ALLOWALL'

# CORS Headers (if needed for API calls from different origins)
# CORS_ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.com",
#     "http://localhost:3000",
# ]
# CORS_ALLOW_METHODS = [
#     "DELETE",
#     "GET",
#     "OPTIONS",
#     "POST",
#     "PUT",
# ]
# CORS_ALLOW_HEADERS = [
#     "accept",
#     "accept-encoding",
#     "authorization",
#     "content-type",
#     "dnt",
#     "origin",
#     "user-agent",
#     "x-csrftoken",
#     "x-requested-with",
# ]
# CORS_ALLOW_CREDENTIALS = True

