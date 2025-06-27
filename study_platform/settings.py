from pathlib import Path
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv # لاستخدام ملف .env محلياً

# NEW: استيراد gettext_lazy للترجمة في هذا الملف
from django.utils.translation import gettext_lazy as _

# تحميل متغيرات البيئة من ملف .env للاختبار المحلي (إذا كان موجوداً)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- إعدادات الأمان الأساسية ---
# SECRET_KEY: يجب أن تكون سرية جداً، ويفضل أن تُقرأ من متغيرات البيئة في الإنتاج.
SECRET_KEY = os.environ.get('SECRET_KEY', '0nPNq5cbMmsK2MQRSW3aO27GB-pMw5pe8m5d7hLcEVNbRriYx-nG4-sQZPpy8rU-kwE') # قم بتغيير هذا في الإنتاج

# DEBUG: يجب أن تكون False في الإنتاج!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 't')

# ALLOWED_HOSTS: أسماء النطاقات التي يمكن لتطبيقك الاستجابة لها.
ALLOWED_HOSTS = []
KOYEB_PUBLIC_HOST = os.environ.get('DJANGO_ALLOWED_HOST')
if KOYEB_PUBLIC_HOST:
    ALLOWED_HOSTS.append(KOYEB_PUBLIC_HOST)
# أضف localhost و 127.0.0.1 للتطوير المحلي فقط
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

# CSRF_TRUSTED_ORIGINS (مهم جداً في الإنتاج لمنع هجمات CSRF)
# يجب أن تتطابق مع البروتوكول والنطاق الذي يصل منه المستخدمون.
CSRF_TRUSTED_ORIGINS = []
if not DEBUG and KOYEB_PUBLIC_HOST:
    CSRF_TRUSTED_ORIGINS.append(f'https://{KOYEB_PUBLIC_HOST}')
elif DEBUG:
    CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])

# X_FRAME_OPTIONS: لإصلاح مشكلة iframe في بيئة Canvas/Koyeb
X_FRAME_OPTIONS = 'ALLOWALL'

# --- تعريف التطبيقات (المهم هنا) ---
# ملاحظة هامة: لكل تطبيق مدرج هنا مثل 'accounts.apps.AccountsConfig'،
# يجب أن يكون لديك ملف 'apps.py' داخل مجلد التطبيق (مثال: accounts/apps.py)
# وهذا الملف يجب أن يحتوي على كلاس AppConfig بالاسم الصحيح (مثال: class AccountsConfig(AppConfig):)
# إذا كان هذا الملف أو الكلاس مفقوداً/غير صحيحاً، فسيؤدي ذلك إلى ModuleNotFoundError.
INSTALLED_APPS = [
    # تطبيقات Django الأساسية
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # يستخدم لتخديم الملفات الثابتة محلياً أثناء التطوير مع Whitenoise
    'django.contrib.staticfiles',

    # تطبيقات الطرف الثالث
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks', # تم التأكد من وجوده في requirements.txt

    # تطبيقاتك الخاصة (الآن مسارات صحيحة بناءً على هيكلية مشروعك)
    'accounts.apps.AccountsConfig', # افتراض أن accounts لديها ملف apps.py
    'achievements.apps.AchievementsConfig',
    'core.apps.CoreConfig',
    'exam_prep.apps.ExamPrepConfig',
    'files_manager.apps.FilesManagerConfig',
    'news.apps.NewsConfig',
    'notes.apps.NotesConfig',
    'tasks.apps.TasksConfig', # تأكد أن هذا السطر يشير إلى apps.py بشكل صحيح إذا كان TasksConfig موجودًا
    # إذا كان لديك تطبيق homepage منفصل عن core، أضفه هنا
    # 'homepage', # إذا كانت homepage تطبيقاً مستقلاً
]

# --- إعدادات Crispy Forms ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5" # تم تغيير crispy_default_template_pack إلى crispy_template_pack

# --- Middleware (طبقات الوسيط) ---
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

# --- إعدادات URL الرئيسية ---
ROOT_URLCONF = 'study_platform.urls'

# --- إعدادات القوالب (Templates) ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # مجلد القوالب الرئيسي للمشروع
        'APP_DIRS': True, # للبحث عن القوالب داخل مجلدات 'templates' في كل تطبيق
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media', # مهم للوصول إلى MEDIA_URL في القوالب
                # 'core.context_processors.common_context', # إذا كان لديك هذا في core
            ],
        },
    },
]

# --- إعدادات WSGI (للإنتاج) ---
WSGI_APPLICATION = 'study_platform.wsgi.application'

# --- إعدادات قاعدة البيانات ---
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

# تأكيد وجود قاعدة بيانات افتراضية (يجب أن يعمل هذا الآن مع منطق SQLite أعلاه)
if 'default' not in DATABASES or 'ENGINE' not in DATABASES['default']:
    raise ImproperlyConfigured("DATABASE_URL environment variable is not set or improperly configured. Please provide a valid PostgreSQL URL or ensure local SQLite setup is correct.")


# --- مصادقة كلمات المرور (Password Validation) ---
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# --- الترجمة والعولمة (Internationalization) ---
LANGUAGE_CODE = 'ar' # تعيين اللغة الافتراضية إلى العربية (تم إصلاح خطأ الاسم هنا)
TIME_ZONE = 'Asia/Riyadh' # تعيين المنطقة الزمنية الخاصة بك

USE_I18N = True # تفعيل الترجمة
USE_TZ = True # تفعيل دعم المناطق الزمنية

# قائمة اللغات المدعومة
LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale', # مسار ملفات الترجمة
]

# --- الملفات الثابتة (Static Files) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_collected' # المجلد الذي سيجمع فيه collectstatic الملفات
STATICFILES_DIRS = [
    BASE_DIR / 'static', # مجلد الملفات الثابتة في جذر المشروع
]
# يستخدم Whitenoise لخدمة الملفات الثابتة بشكل فعال في الإنتاج
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- ملفات الوسائط (Media Files - المرفوعة من المستخدمين) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # المجلد الذي ستُخزن فيه الملفات المرفوعة محلياً

# هذا السطر مهم جداً: تأكد أنه غير موجود أو معلق عليه إذا كنت لا تستخدم Cloudinary
# DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# --- إعدادات المصادقة (Authentication) ---
LOGIN_URL = 'accounts:login' # مسار صفحة تسجيل الدخول
LOGIN_REDIRECT_URL = 'homepage:home' # المسار بعد تسجيل الدخول بنجاح (افترضت homepage هنا)
LOGOUT_REDIRECT_URL = 'accounts:login' # المسار بعد تسجيل الخروج

# --- إعدادات المفتاح الأساسي الافتراضي (Default Primary Key Field) ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- فرض HTTPS في الإنتاج (إذا كان DEBUG=False) ---
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- إعدادات التسجيل (Logging) ---
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
        '': { # لـ loggers التطبيق الأخرى (مثل تطبيقاتك الخاصة)
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
