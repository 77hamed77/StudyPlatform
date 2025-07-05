from django.db import models
from django.contrib.auth import get_user_model
from files_manager.models import MainFile
from django.utils.translation import gettext_lazy as _

User = get_user_model() # الحصول على نموذج المستخدم النشط

class ChatInteraction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_interactions',
        verbose_name=_("المستخدم")
    )
    main_file = models.ForeignKey(
        MainFile,
        on_delete=models.CASCADE,
        related_name='chat_interactions',
        verbose_name=_("المحاضرة"),
        null=True,
        blank=True
    )
    question = models.TextField(
        verbose_name=_("السؤال")
    )
    answer = models.TextField(
        verbose_name=_("الإجابة"),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("تاريخ التفاعل")
    )

    class Meta:
        verbose_name = _("تفاعل شات")
        verbose_name_plural = _("تفاعلات الشات")
        ordering = ['-created_at'] # ترتيب التفاعلات من الأحدث إلى الأقدم

    def __str__(self):
        """تمثيل السلسلة للنموذج."""
        return f"{self.user.username} - {self.question[:50]}..."

    def save(self, *args, **kwargs):
        """
        حفظ التفاعل مع التحقق من وجود المستخدم.
        هذا التحقق يضمن أن كل تفاعل مرتبط بمستخدم.
        """
        if not self.user:
            raise ValueError(_("يجب تحديد المستخدم."))
        super().save(*args, **kwargs)

    def get_answer_preview(self):
        """إرجاع معاينة للإجابة (أول 100 حرف)."""
        if self.answer:
            return self.answer[:100] + '...' if len(self.answer) > 100 else self.answer
        return _("لا توجد إجابة بعد.")

    def get_question_preview(self):
        """إرجاع معاينة للسؤال (أول 100 حرف)."""
        if self.question:
            return self.question[:100] + '...' if len(self.question) > 100 else self.question
        return _("لا يوجد سؤال بعد.")

    def get_file_name(self):
        """إرجاع اسم الملف المرتبط بالتفاعل."""
        if self.main_file:
            # افتراض أن MainFile لديه حقل 'file' من نوع FileField
            return self.main_file.file.name if hasattr(self.main_file, 'file') else _("لا يوجد اسم ملف.")
        return _("لا يوجد ملف مرتبط.")

    def get_file_url(self):
        """إرجاع رابط الملف المرتبط بالتفاعل."""
        if self.main_file and hasattr(self.main_file, 'file') and self.main_file.file:
            return self.main_file.file.url
        return None

    def get_file_type(self):
        """إرجاع نوع الملف المرتبط بالتفاعل."""
        if self.main_file and hasattr(self.main_file, 'file_type'):
            return self.main_file.file_type
        return _("لا يوجد نوع ملف مرتبط.")

    def get_file_size(self):
        """إرجاع حجم الملف المرتبط بالتفاعل."""
        if self.main_file and hasattr(self.main_file, 'file_size'):
            return self.main_file.file_size
        return _("لا يوجد حجم ملف مرتبط.")

    def get_file_description(self):
        """إرجاع وصف الملف المرتبط بالتفاعل."""
        if self.main_file and hasattr(self.main_file, 'description'):
            return self.main_file.description
        return _("لا يوجد وصف ملف مرتبط.")

    def get_file_semester(self):
        """إرجاع الفصل الدراسي للملف المرتبط."""
        if self.main_file and hasattr(self.main_file, 'semester'):
            return self.main_file.semester
        return _("لا يوجد فصل دراسي مرتبط.")

    def get_file_year(self):
        """إرجاع السنة الدراسية للملف المرتبط (تم التصحيح إلى academic_year)."""
        if self.main_file and hasattr(self.main_file, 'academic_year'):
            return self.main_file.academic_year
        return _("لا يوجد سنة دراسية مرتبطة.")

    def get_file_instructor(self):
        """إرجاع اسم المحاضر للملف المرتبط (تم التصحيح إلى lecturer)."""
        if self.main_file and hasattr(self.main_file, 'lecturer'):
            # افتراض أن المحاضر لديه سمة 'name' أو 'username'
            return self.main_file.lecturer.name if hasattr(self.main_file.lecturer, 'name') else str(self.main_file.lecturer)
        return _("لا يوجد محاضر مرتبط.")

    def get_file_department(self):
        """إرجاع قسم الملف المرتبط."""
        if self.main_file and hasattr(self.main_file, 'department'):
            return self.main_file.department
        return _("لا يوجد قسم مرتبط.")

