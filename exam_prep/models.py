from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model # لاستخدام نموذج المستخدم
from django.contrib.contenttypes.fields import GenericForeignKey # للربط العام
from django.contrib.contenttypes.models import ContentType # للربط العام
from django.utils import timezone # لاستخدام التوقيت في الحقول الزمنية

User = get_user_model() # الحصول على نموذج المستخدم الحالي

class ExamPrayer(models.Model):
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("عنوان الدعاء (اختياري)")
    )
    text = models.TextField(verbose_name=_("نص الدعاء"))
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
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
        ordering = ['order', 'id']

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
        max_length=255,
        verbose_name=_("عنوان النصيحة/الترتيب")
    )
    description = models.TextField(verbose_name=_("شرح النصيحة/الترتيب"))
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name=_("تصنيف النصيحة"),
        db_index=True
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

    class Meta:
        verbose_name = _("نصيحة/ترتيب امتحان")
        verbose_name_plural = _("نصائح وترتيبات الامتحانات")
        ordering = ['category', 'order', 'id']

    def __str__(self):
        return self.title

# --- New Admin and Analytics Models ---

class Report(models.Model):
    """
    نموذج للإبلاغ عن المحتوى غير اللائق من قبل المستخدمين.
    يمكن أن يرتبط بأي نوع من المحتوى في المنصة باستخدام GenericForeignKey.
    """
    STATUS_CHOICES = (
        ('pending', _('معلق')),
        ('reviewed', _('تمت المراجعة')),
        ('resolved', _('تم الحل')),
        ('rejected', _('مرفوض')),
    )

    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_reports',
        verbose_name=_("المُبلغ")
    )
    
    # Generic Foreign Key لربط الإبلاغ بأي كائن في المنصة
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("نوع المحتوى المبلغ عنه")
    )
    object_id = models.PositiveIntegerField(verbose_name=_("معرف الكائن المبلغ عنه"))
    content_object = GenericForeignKey('content_type', 'object_id') # الكائن الفعلي المبلغ عنه

    reason = models.TextField(verbose_name=_("سبب الإبلاغ"))
    reported_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإبلاغ"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("الحالة")
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports',
        verbose_name=_("تمت المراجعة بواسطة")
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاريخ المراجعة"))
    admin_notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات المشرف"))

    class Meta:
        verbose_name = _("إبلاغ")
        verbose_name_plural = _("إبلاغات")
        ordering = ['status', '-reported_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', '-reported_at']),
        ]

    def __str__(self):
        reporter_name = self.reporter.username if self.reporter else 'مجهول'
        return f"إبلاغ من {reporter_name} عن {self.content_object} - الحالة: {self.get_status_display()}"


class UserActivity(models.Model):
    """
    يسجل أنشطة المستخدمين المختلفة لأغراض التحليلات والإحصائيات.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_("المستخدم")
    )
    activity_type = models.CharField(
        max_length=100,
        verbose_name=_("نوع النشاط"),
        help_text=_("مثال: 'login', 'file_view', 'task_completed', 'group_message'")
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("التاريخ والوقت"))
    
    # Generic foreign key لربط النشاط بكائن معين (اختياري)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("نوع الكائن المرتبط")
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("معرف الكائن المرتبط")
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    details = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name=_("تفاصيل إضافية"),
        help_text=_("بيانات JSON إضافية حول النشاط (مثل مدة المشاهدة، حجم الملف، نتيجة الاختبار).")
    )

    class Meta:
        verbose_name = _("نشاط المستخدم")
        verbose_name_plural = _("أنشطة المستخدمين")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['activity_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} في {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

