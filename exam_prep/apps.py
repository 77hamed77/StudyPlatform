from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ExamPrepConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exam_prep'
    verbose_name = _("الاستعداد للامتحانات") # إضافة اسم وصفي للتطبيق