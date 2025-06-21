from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AchievementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'achievements'
    verbose_name = _("الإنجازات والشارات") # اسم وصفي للتطبيق

    def ready(self):
        # استيراد الإشارات عند بدء تشغيل التطبيق
        try:
            import achievements.signals
        except ImportError:
            # هذا طبيعي إذا كان ملف signals.py غير موجود بعد أو به خطأ مؤقت
            pass