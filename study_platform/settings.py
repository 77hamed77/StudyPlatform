from pathlib import Path
import os
import dj_database_url
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'fallback_secret_key_for_development_only_123!@#abc' # استبدل هذا بمفتاح قوي أو قم بإزالته إذا كنت ستعتمد كليًا على متغير البيئة
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG_VALUE = os.environ.get('DJANGO_DEBUG', 'False')
DEBUG = DEBUG_VALUE.lower() in ('true', '1', 't')


ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

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
    # تطبيقاتك
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
                'django.contrib.messages.context_processors.messages', # <--- تأكد أن هذا السطر موجود وصحيح تمامًا
                'core.context_processors.common_context',
            ],
        },
    },
]
WSGI_APPLICATION = 'study_platform.wsgi.application'


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

# استخدم dj_database_url لقراءة DATABASE_URL من متغيرات البيئة
# مع قيمة افتراضية لـ SQLite للتطوير المحلي إذا لم يتم العثور على DATABASE_URL
# في الإنتاج، يجب تعيين DATABASE_URL كمتغير بيئة على Render
# قم بتغيير القيمة الافتراضية هنا إلى URI قاعدة بيانات Supabase الخاصة بك للتطوير المحلي
# أو اتركها لـ SQLite إذا كنت تفضل التبديل بينهما يدويًا في التكوين المحلي
DEFAULT_DATABASE_URL = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}")

DATABASES = {
    'default': dj_database_url.config(
        default=DEFAULT_DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh' # تأكد من أن هذه هي منطقتك الزمنية الصحيحة

USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_collected')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Media files (Uploaded by users)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Authentication settings
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'
LOGIN_URL = 'login'


# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF_TRUSTED_ORIGINS (مهم إذا كنت تستخدم HTTPS على Render)
CSRF_TRUSTED_ORIGINS_ENV = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS')
if CSRF_TRUSTED_ORIGINS_ENV:
    CSRF_TRUSTED_ORIGINS = [CSRF_TRUSTED_ORIGINS_ENV]
elif RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}']
else:
    CSRF_TRUSTED_ORIGINS = []

# لإجبار الاتصالات على HTTPS في الإنتاج (إذا كان DEBUG=False)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True