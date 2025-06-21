from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = _("النواة والتطبيق الأساسي") # اسم وصفي للتطبيق

    def ready(self):
        # استيراد الإشارات إذا كان لديك أي إشارات معرفة في core/signals.py
        try:
            import core.signals
        except ImportError:
            pass