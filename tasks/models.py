from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# افتراض أن موديل Subject موجود في تطبيق files_manager أو تطبيق مشابه
try:
    from files_manager.models import Subject
except ImportError:
    class Subject(models.Model): # بديل بسيط
        name = models.CharField(max_length=100, unique=True)
        def __str__(self): return self.name
        class Meta:
            verbose_name = _("مادة دراسية (بديل)")
            verbose_name_plural = _("مواد دراسية (بديل)")


class Task(models.Model):
    STATUS_CHOICES = [ # معرف داخل الكلاس
        ('pending', _('قيد الانتظار')),
        ('in_progress', _('قيد التنفيذ')),
        ('completed', _('مكتملة')),
        ('postponed', _('مؤجلة')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks_set',
        verbose_name=_("المستخدم")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("عنوان المهمة")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("وصف المهمة")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("المادة الدراسية المرتبطة")
    )
    due_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("الموعد النهائي")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES, # استخدامه هنا صحيح
        default='pending',
        verbose_name=_("حالة المهمة"),
        db_index=True
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("تاريخ الإنشاء")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("تاريخ آخر تحديث")
    )

    class Meta:
        verbose_name = _("مهمة")
        verbose_name_plural = _("مهام")
        ordering = ['due_date', 'created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'due_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return timezone.now() > self.due_date
        return False