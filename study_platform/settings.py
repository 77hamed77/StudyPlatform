# study_platform/settings.py

from pathlib import Path
import os
import dj_database_url # لاستيراد dj_database_url
from django.utils.translation import gettext_lazy as _ # للترجمة (جيد إبقاؤه)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# اقرأ SECRET_KEY من متغير بيئة، مع قيمة افتراضية للتطوير المحلي فقط
# قم بإنشاء مفتاح قوي واستخدمه كقيمة افتراضية أو لا تضع قيمة افتراضية واجعله إلزاميًا في متغيرات البيئة للإنتاج
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'fallback_secret_key_for_development_only_123!@#abc' # استبدل هذا بمفتاح قوي أو قم بإزالته إذا كنت ستعتمد كليًا على متغير البيئة
)

# SECURITY WARNING: don't run with debug turned on in production!
# اقرأ DEBUG من متغير بيئة، افتراضيًا يكون False للإنتاج
# على Render، قم بتعيين DJANGO_DEBUG=False للإنتاج، ويمكنك تركه غير مُعين أو DJANGO_DEBUG=True للتطوير المحلي
# التحويل إلى boolean بشكل صحيح
DEBUG_VALUE = os.environ.get('DJANGO_DEBUG', 'False') # الافتراضي هو 'False' للإنتاج
DEBUG = DEBUG_VALUE.lower() in ('true', '1', 't')


ALLOWED_HOSTS = []
# Render يضبط متغير بيئة RENDER_EXTERNAL_HOSTNAME تلقائيًا
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# أضف localhost و 127.0.0.1 للتطوير المحلي
# لا تضف '*' في الإنتاج
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])
# إذا لم يتم تعيين أي شيء (مثل في الإنتاج بدون RENDER_EXTERNAL_HOSTNAME محدد بعد)،
# يمكنك إضافة قيمة افتراضية أو تركها فارغة لتسبب خطأ (وهو أفضل للأمان)
# إذا كانت ALLOWED_HOSTS فارغة و DEBUG = False، لن يعمل Django.


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # يجب أن يكون أعلى من staticfiles للاستخدام مع runserver
    'django.contrib.staticfiles',    # Django's own staticfiles app
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
    'whitenoise.middleware.WhiteNoiseMiddleware', # <--- بعد SecurityMiddleware وقبل معظم الـ middleware الأخرى
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # إذا كنت تستخدم ترجمة
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
                'core.context_processors.common_context', # تأكد أن هذا هو معالج السياق الصحيح
            ],
        },
    },
]

WSGI_APPLICATION = 'study_platform.wsgi.application'


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

# استخدم dj_database_url لقراءة DATABASE_URL من متغيرات البيئة
# مع قيمة افتراضية لـ SQLite للتطوير المحلي إذا لم يتم العثور على DATABASE_URL
DEFAULT_SQLITE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"
DATABASES = {
    'default': dj_database_url.config(
        default=DEFAULT_SQLITE_URL,
        conn_max_age=600, # مدة بقاء الاتصال (ثواني)
        conn_health_checks=True, # (لـ dj-database-url >= 1.0)
    )
}

# إذا كنت تريد استخدام MySQL محليًا كاحتياطي إذا لم يتم تعيين DATABASE_URL (بدلاً من SQLite)
# if 'DATABASE_URL' not in os.environ:
#     DATABASES['default'] = {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'platform_mystudents_db', # اسم قاعدة بيانات MySQL المحلية
#         'USER': os.environ.get('LOCAL_DB_USER', 'hamid'), # اقرأ من متغير بيئة محلي أو استخدم قيمة ثابتة
#         'PASSWORD': os.environ.get('LOCAL_DB_PASSWORD', 'rax111rax'), # اقرأ من متغير بيئة محلي
#         'HOST': os.environ.get('LOCAL_DB_HOST', 'localhost'),
#         'PORT': os.environ.get('LOCAL_DB_PORT', '3306'),
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#             'charset': 'utf8mb4',
#         },
#     }


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

LANGUAGE_CODE = 'ar' # تم التغيير إلى العربية كلغة افتراضية
# LANGUAGES = [
#     ('ar', _('العربية')),
#     ('en', _('English')),
# ]
# LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')] # إذا كان لديك ملفات ترجمة

TIME_ZONE = 'Asia/Riyadh' # مثال، قم بتغييره إلى منطقتك الزمنية المفضلة

USE_I18N = True # تفعيل الترجمة

USE_TZ = True # تفعيل دعم المناطق الزمنية (موصى به)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = '/static/'
# المجلد الذي سيتم فيه جمع كل الملفات الثابتة عند تشغيل collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_collected')

# المجلدات الإضافية التي يبحث فيها Django عن الملفات الثابتة (بالإضافة لمجلد static داخل كل تطبيق)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# إعدادات WhiteNoise لخدمة الملفات الثابتة في الإنتاج
# تأكد من أن whitenoise مضاف في MIDDLEWARE
# يجعل WhiteNoise يخدم الملفات الثابتة التي تم ضغطها (gzipped) ونسخها مع أسماء فريدة (manifest)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Media files (Uploaded by users)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# في الإنتاج، يُفضل استخدام خدمة تخزين خارجية لملفات الميديا (مثل AWS S3)


# Authentication settings
LOGIN_REDIRECT_URL = 'core:dashboard' # المسار الذي يتم توجيه المستخدم إليه بعد تسجيل الدخول بنجاح
LOGOUT_REDIRECT_URL = 'core:home'   # المسار الذي يتم توجيه المستخدم إليه بعد تسجيل الخروج
LOGIN_URL = 'login'                 # اسم الـ URL لصفحة تسجيل الدخول (من django.contrib.auth.urls)


# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF_TRUSTED_ORIGINS (مهم إذا كنت تستخدم HTTPS على Render)
# Render قد توفر اسم النطاق عبر متغير بيئة
# أو يمكنك إضافته يدويًا بعد معرفة نطاق .onrender.com الخاص بك
CSRF_TRUSTED_ORIGINS_ENV = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS')
if CSRF_TRUSTED_ORIGINS_ENV:
    CSRF_TRUSTED_ORIGINS = [CSRF_TRUSTED_ORIGINS_ENV]
elif RENDER_EXTERNAL_HOSTNAME: # استخدام نفس متغير ALLOWED_HOSTS
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}']
else:
    CSRF_TRUSTED_ORIGINS = [] # اتركها فارغة للتطوير المحلي إذا لم تكن تستخدم HTTPS

# لإجبار الاتصالات على HTTPS في الإنتاج (إذا كان DEBUG=False)
# هذا يعمل بشكل جيد إذا كان Render يتعامل مع إنهاء SSL/TLS
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True