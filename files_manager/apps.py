from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class FilesManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files_manager'
    verbose_name = _("إدارة الملفات والمصادر") # إضافة اسم وصفي للتطبيق