from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import os
from cloudinary_storage.storage import MediaCloudinaryStorage

# --- موديلات أساسية ---
class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("اسم المادة")
    )
    class Meta:
        verbose_name = _("مادة دراسية")
        verbose_name_plural = _("مواد دراسية")
        ordering = ['name']
    def __str__(self):
        return self.name

class Lecturer(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name=_("اسم المحاضر")
    )
    class Meta:
        verbose_name = _("محاضر")
        verbose_name_plural = _("محاضرون")
        ordering = ['name']
    def __str__(self):
        return self.name

class FileType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("نوع الملف")
    )
    class Meta:
        verbose_name = _("نوع ملف")
        verbose_name_plural = _("أنواع الملفات")
        ordering = ['name']
    def __str__(self):
        return self.name

# --- موديل الملفات الرئيسية (يرافعها المشرفون) ---
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_(f"امتداد الملف '{ext}' غير مدعوم. الامتدادات المسموح بها: {', '.join(valid_extensions)}"))

def validate_file_size(value):
    limit = 10 * 1024 * 1024
    if value.size > limit:
        raise ValidationError(_(f"حجم الملف كبير جدًا. الحد الأقصى المسموح به هو {limit / (1024*1024)}MB."))


class MainFile(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_("عنوان الملف")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("الوصف (اختياري)")
    )
    file = models.FileField(
        upload_to='main_files/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
        verbose_name=_("الملف"),
        storage=MediaCloudinaryStorage()
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_main_files',
        verbose_name=_("رُفع بواسطة (المسؤول)")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("تاريخ الرفع")
    )
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
        # هذا لا يزال يشير إلى صفحة تفاصيل Django الداخلية
        return reverse('files_manager:main_file_detail', kwargs={'pk': self.pk})

    @property
    def file_extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()

    # NEW: override the url property for the FileField
    @property
    def file_url(self):
        # Accessing .url on the FileField object should return the Cloudinary URL
        # We define a separate property to ensure we always get the Cloudinary URL
        if self.file:
            return self.file.url
        return None # أو رابط Placeholder إذا أردت

# --- موديل ملخصات الطلاب ---
class StudentSummary(models.Model):
    STATUS_CHOICES = [
        ('pending', _('بانتظار المراجعة')),
        ('approved', _('معتمد')),
        ('rejected', _('مرفوض')),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name=_("عنوان الملخص")
    )
    file = models.FileField(
        upload_to='student_summaries/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
        verbose_name=_("ملف الملخص"),
        storage=MediaCloudinaryStorage()
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='student_summaries',
        verbose_name=_("المادة الدراسية")
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_student_summaries',
        verbose_name=_("رُفع بواسطة الطالب")
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الرفع"))
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("حالة الملخص"),
        db_index=True
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("ملاحظات المشرف (سبب الرفض مثلاً)")
    )
    class Meta:
        verbose_name = _("ملخص طالب")
        verbose_name_plural = _("ملخصات الطلاب")
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_by', 'status']),
            models.Index(fields=['subject', 'status']),
        ]

    def __str__(self):
        return f"{self.title} - (بواسطة: {self.uploaded_by.username})"

    @property
    def is_approved(self):
        return self.status == 'approved'

    # NEW: override the url property for the FileField
    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None # أو رابط Placeholder إذا أردت


# --- موديل تفاعلات المستخدم مع الملفات (لتمييز كمقروء) ---
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
        return f"{self.user.username} - {self.main_file.title} (مقروء: {self.marked_as_read})"
