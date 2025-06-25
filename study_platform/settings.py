# study_platform/settings.py
from pathlib import Path
import os
import dj_database_url # لاستيراد dj_database_url

# NEW: تحميل متغيرات البيئة من ملف .env للاختبار المحلي
# تأكد من تثبيت python-dotenv: pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
# ---------------------------------------------------------------------------

from django.utils.translation import gettext_lazy as _ # للترجمة (جيد إبقاؤه)

# مسارات البناء داخل المشروع
BASE_DIR = Path(__file__).resolve().parent.parent


# إعدادات التطوير السريع - غير مناسبة للإنتاج
# راجع https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

# تحذير أمني: حافظ على سرية المفتاح السري المستخدم في الإنتاج!
# اقرأ SECRET_KEY من متغير بيئة، مع قيمة افتراضية للتطوير المحلي فقط
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'insecure-fallback-secret-key-for-local-development-only-replace-me-12345' # !!! هام: قم بتغيير هذا لمفتاح سري فريد إذا كنت ستستخدمه حتى في الإنتاج الصغير !!!
)

# تحذير أمني: لا تقم بتشغيل DEBUG في وضع الإنتاج!
# اقرأ DEBUG من متغير بيئة، افتراضيًا يكون False للإنتاج
# على Koyeb، قم بتعيين DJANGO_DEBUG=False للإنتاج.
# محليًا، يمكنك تعيين DJANGO_DEBUG=True في ملف .env الخاص بك.
DEBUG_VALUE = os.environ.get('DJANGO_DEBUG', 'False')
DEBUG = DEBUG_VALUE.lower() in ('true', '1', 't')


ALLOWED_HOSTS = []
# Koyeb (أو Render سابقاً) يضبط متغير بيئة لاسم المضيف الخارجي.
# يمكن أن يكون RENDER_EXTERNAL_HOSTNAME، KOYEB_EXTERNAL_HOSTNAME، أو ما شابه.
# ابحث عن اسم المتغير في وثائق Koyeb أو سجلات النشر.
EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME') or \
                    os.environ.get('KOYEB_EXTERNAL_HOSTNAME') # مثال لمتغير Koyeb
if EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(EXTERNAL_HOSTNAME)

# أضف localhost و 127.0.0.1 للتطوير المحلي فقط
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])


# تعريف التطبيقات

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # يجب أن يكون أعلى من staticfiles للاستخدام مع runserver
    'django.contrib.staticfiles',    # Django's own staticfiles app
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

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_DEFAULT_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <--- بعد SecurityMiddleware وقبل معظم الـ middleware الأخرى
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # إذا كنت تستخدم ترجمة
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', # <--- تم إصلاح هذا السطر
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
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

# استخدم dj_database_url لقراءة DATABASE_URL من متغيرات البيئة
# محليًا، إذا لم يتم تعيين DATABASE_URL (مثلاً في ملف .env)، فسيستخدم SQLite.
# في الإنتاج على Render أو Koyeb، يجب تعيين DATABASE_URL كمتغير بيئة ليشير إلى Supabase.
DEFAULT_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', DEFAULT_DATABASE_URL),
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

# CSRF_TRUSTED_ORIGINS (مهم إذا كنت تستخدم HTTPS في الإنتاج)
# Render/Koyeb قد توفر اسم النطاق عبر متغير بيئة.
CSRF_TRUSTED_ORIGINS_ENV = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS')
if CSRF_TRUSTED_ORIGINS_ENV:
    CSRF_TRUSTED_ORIGINS = [CSRF_TRUSTED_ORIGINS_ENV]
elif EXTERNAL_HOSTNAME: # استخدام متغير EXTERNAL_HOSTNAME الجديد
    CSRF_TRUSTED_ORIGINS = [f'https://{EXTERNAL_HOSTNAME}']
else:
    CSRF_TRUSTED_ORIGINS = []

# لإجبار الاتصالات على HTTPS في الإنتاج (إذا كان DEBUG=False)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True