from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class NotesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notes'
    verbose_name = _("الملاحظات السريعة") # إضافة اسم وصفي للتطبيق