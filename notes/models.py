from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class NoteCategory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='note_categories', # اسم أوضح للعلاقة العكسية
        verbose_name=_("المستخدم")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("اسم التصنيف")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء")) # إضافة تاريخ الإنشاء

    class Meta:
        verbose_name = _("تصنيف ملاحظة")
        verbose_name_plural = _("تصنيفات الملاحظات")
        unique_together = ('user', 'name') # لضمان أن كل مستخدم لديه أسماء تصنيفات فريدة
        ordering = ['user', 'name'] # ترتيب افتراضي

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # عادة لا نحتاج لصفحة تفاصيل لتصنيف، لكن يمكن توجيهه لقائمة الملاحظات المفلترة بهذا التصنيف
        return reverse('notes:note_list') + f'?category={self.pk}'


class QuickNote(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quick_notes', # اسم أوضح للعلاقة العكسية
        verbose_name=_("المستخدم")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("عنوان الملاحظة")
    )
    content = models.TextField(verbose_name=_("محتوى الملاحظة"))
    category = models.ForeignKey(
        NoteCategory,
        on_delete=models.SET_NULL, # إذا حُذف التصنيف، لا تُحذف الملاحظة، بل يُضبط التصنيف إلى NULL
        null=True,
        blank=True,
        related_name='notes', # علاقة عكسية من التصنيف للملاحظات
        verbose_name=_("التصنيف")
    )
    created_at = models.DateTimeField(
        default=timezone.now, # استخدام default للسماح بتعديله إذا لزم الأمر
        verbose_name=_("تاريخ الإنشاء")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("تاريخ آخر تحديث")
    )

    class Meta:
        verbose_name = _("ملاحظة سريعة")
        verbose_name_plural = _("ملاحظات سريعة")
        ordering = ['-updated_at', '-created_at'] # الأحدث تحديثًا أو إنشاءً أولاً
        indexes = [
            models.Index(fields=['user', 'updated_at']), # فهرس لتحسين جلب ملاحظات المستخدم مرتبة
            models.Index(fields=['user', 'category']),   # فهرس لتحسين فلترة الملاحظات بالتصنيف للمستخدم
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        يُرجع المسار URL للوصول إلى تفاصيل هذه الملاحظة.
        """
        return reverse('notes:note_detail', kwargs={'pk': self.pk})