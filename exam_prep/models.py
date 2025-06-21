from django.db import models
from django.utils.translation import gettext_lazy as _

class ExamPrayer(models.Model):
    title = models.CharField(
        max_length=200,
        blank=True, # العنوان اختياري
        verbose_name=_("عنوان الدعاء (اختياري)")
    )
    text = models.TextField(verbose_name=_("نص الدعاء"))
    order = models.PositiveIntegerField(
        default=0,
        db_index=True, # إضافة فهرس لتحسين الترتيب
        help_text=_("لتحديد ترتيب ظهور الدعاء (الأقل أولاً).")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشط (معروض)؟"),
        help_text=_("إلغاء التحديد لإخفاء الدعاء مؤقتًا.")
    )

    class Meta:
        verbose_name = _("دعاء امتحان")
        verbose_name_plural = _("أدعية الامتحانات")
        ordering = ['order', 'id'] # الترتيب الافتراضي

    def __str__(self):
        return self.title if self.title else _(f"دعاء رقم {self.id}")


class ExamTip(models.Model):
    CATEGORY_CHOICES = [
        ('general', _('نصائح عامة/ترتيبات')),
        ('before', _('قبل الامتحان (مذاكرة)')),
        ('during', _('أثناء الامتحان')),
        ('after', _('بعد الامتحان')),
    ]

    title = models.CharField(
        max_length=255, # زيادة الطول قليلاً
        verbose_name=_("عنوان النصيحة/الترتيب")
    )
    description = models.TextField(verbose_name=_("شرح النصيحة/الترتيب"))
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name=_("تصنيف النصيحة"),
        db_index=True # إضافة فهرس لتحسين الفلترة حسب التصنيف
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text=_("لتحديد ترتيب ظهور النصيحة داخل تصنيفها (الأقل أولاً).")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشطة (معروضة)؟"),
        help_text=_("إلغاء التحديد لإخفاء النصيحة مؤقتًا.")
    )
    # يمكنك إضافة حقل 'المصدر' إذا كانت النصائح من مصادر خارجية
    # source = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("المصدر"))

    class Meta:
        verbose_name = _("نصيحة/ترتيب امتحان")
        verbose_name_plural = _("نصائح وترتيبات الامتحانات")
        ordering = ['category', 'order', 'id'] # الترتيب الافتراضي

    def __str__(self):
        return self.title