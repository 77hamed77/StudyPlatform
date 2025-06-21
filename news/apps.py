from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'
    verbose_name = _("الأخبار والإعلانات") # اسم وصفي للتطبيق

    def ready(self):
        # استيراد الإشارات عند بدء تشغيل التطبيق
        try:
            import news.signals
        except ImportError:
            pass # تجاهل إذا لم يكن ملف signals.py موجودًا بعد