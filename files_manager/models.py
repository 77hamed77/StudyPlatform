# files_manager/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
import os

User = get_user_model()

# --- Validators ---
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = [
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
        '.txt', '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif'
    ]
    if ext not in valid_extensions:
        raise ValidationError(
            _("امتداد الملف '%(ext)s' غير مدعوم. الامتدادات المسموح بها: %(allowed)s."),
            params={'ext': ext, 'allowed': ', '.join(valid_extensions)},
        )

def validate_file_size(value):
    limit = 10 * 1024 * 1024  # 10 ميجابايت
    if value.size > limit:
        raise ValidationError(
            _("حجم الملف كبير جدًا. الحد الأقصى المسموح به هو %(max)sMB."),
            params={'max': int(limit / (1024 * 1024))},
        )

# --- موديلات أساسية ---
class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("اسم المادة"))

    class Meta:
        verbose_name = _("مادة دراسية")
        verbose_name_plural = _("مواد دراسية")
        ordering = ['name']

    def __str__(self):
        return self.name

class Lecturer(models.Model):
    name = models.CharField(max_length=150, verbose_name=_("اسم المحاضر"))

    class Meta:
        verbose_name = _("محاضر")
        verbose_name_plural = _("محاضرون")
        ordering = ['name']

    def __str__(self):
        return self.name

class FileType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("نوع الملف"))

    class Meta:
        verbose_name = _("نوع ملف")
        verbose_name_plural = _("أنواع الملفات")
        ordering = ['name']

    def __str__(self):
        return self.name

# --- موديل الملفات الرئيسية (يرفعها المشرفون) ---
class MainFile(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("عنوان الملف"))
    description = models.TextField(blank=True, null=True, verbose_name=_("الوصف (اختياري)"))
    file = models.FileField(
        upload_to='main_files/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
        verbose_name=_("الملف"),
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='main_files',
        verbose_name=_("المادة الدراسية")
    )
    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='main_files',
        verbose_name=_("المحاضر (اختياري)")
    )
    file_type = models.ForeignKey(
        FileType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='main_files',
        verbose_name=_("نوع الملف (اختياري)")
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_main_files',
        verbose_name=_("رُفع بواسطة (المسؤول)")
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الرفع"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث"))

    class Meta:
        verbose_name = _("ملف رئيسي")
        verbose_name_plural = _("الملفات الرئيسية")
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['subject', '-uploaded_at']),
            models.Index(fields=['file_type', '-uploaded_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('files_manager:main_file_detail', kwargs={'pk': self.pk})

    @property
    def file_extension(self):
        if self.file and self.file.name:
            _, extension = os.path.splitext(self.file.name)
            return extension.lower()
        return ""

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

# --- موديل ملخصات الطلاب ---
class StudentSummary(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, _('بانتظار المراجعة')),
        (STATUS_APPROVED, _('معتمد')),
        (STATUS_REJECTED, _('مرفوض')),
    ]

    title = models.CharField(max_length=255, verbose_name=_("عنوان الملخص"))
    file = models.FileField(
        upload_to='student_summaries/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
        verbose_name=_("ملف الملخص"),
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='student_summaries',
        verbose_name=_("المادة الدراسية")
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_student_summaries',
        verbose_name=_("رُفع بواسطة الطالب")
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الرفع"))
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_("حالة الملخص"),
        db_index=True
    )
    admin_notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات المشرف (سبب الرفض مثلاً)"))
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("مشاركة الملخص مع الجميع"),
        help_text=_("إذا تم تحديده، سيكون الملخص متاحًا للجميع بعد الموافقة."),
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name=_("رفع الملخص بشكل مجهول"),
        help_text=_("إذا تم تحديده، سيتم إخفاء اسم المستخدم."),
    )

    class Meta:
        verbose_name = _("ملخص طالب")
        verbose_name_plural = _("ملخصات الطلاب")
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_by', 'status']),
            models.Index(fields=['subject', 'status', 'is_public']),
        ]

    def __str__(self):
        username = self.uploaded_by.username if self.uploaded_by and not self.is_anonymous else "مجهول"
        return f"{self.title} - (بواسطة: {username})"

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    @property
    def file_extension(self):
        if self.file and self.file.name:
            _, extension = os.path.splitext(self.file.name)
            return extension.lower()
        return ""

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

# --- موديل تفاعلات المستخدم مع الملفات ---
class UserFileInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="file_interactions_set")
    main_file = models.ForeignKey(MainFile, on_delete=models.CASCADE, related_name="user_interactions_set")
    marked_as_read = models.BooleanField(default=False, verbose_name=_("تم تمييزه كمقروء/مدروس"))
    marked_at = models.DateTimeField(null=True, blank=True, verbose_name=_("تاريخ التمييز"))

    class Meta:
        unique_together = ('user', 'main_file')
        verbose_name = _("تفاعل مستخدم مع ملف")
        verbose_name_plural = _("تفاعلات المستخدمين مع الملفات")
        ordering = ['-marked_at']

    def __str__(self):
        username = self.user.username if self.user else "-"
        file_title = self.main_file.title if self.main_file else "-"
        return f"{username} - {file_title} (مقروء: {self.marked_as_read})"