from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.urls import reverse # إذا أردت get_absolute_url للشارة

class Badge(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True, # اسم الشارة يجب أن يكون فريدًا
        verbose_name=_("اسم الشارة")
    )
    description = models.TextField(verbose_name=_("وصف الشارة"))
    icon_class = models.CharField(
        max_length=100, # زيادة الطول لاستيعاب أسماء فئات أطول
        blank=True,
        null=True,
        verbose_name=_("فئة CSS للأيقونة (Font Awesome)"),
        help_text=_("مثال: fas fa-star, mdi mdi-trophy. اترك فارغًا إذا استخدمت صورة.")
    )
    icon_image = models.ImageField( # إضافة حقل صورة كبديل للأيقونة
        upload_to='badges_icons/',
        blank=True,
        null=True,
        verbose_name=_("صورة أيقونة الشارة (اختياري)")
    )
    criteria_description = models.TextField( # تغيير لـ TextField لمرونة أكبر
        blank=True,
        null=True,
        verbose_name=_("وصف معيار تحقيق الشارة")
    )
    # حقل لتحديد نوع الشارة إذا أردت ربطها بآليات تلقائية أكثر تعقيدًا
    # أو لتصنيف الشارات
    badge_type_key = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True, # إذا كان سيُستخدم كمفتاح برمجي، يجب أن يكون فريدًا
        db_index=True,
        help_text=_("مفتاح برمجي فريد لنوع الشارة (مثل TASK_COMPLETER_10).")
    )
    order = models.PositiveIntegerField(default=0, db_index=True, help_text=_("لتحديد ترتيب ظهور الشارات."))


    class Meta:
        verbose_name = _("شارة")
        verbose_name_plural = _("شارات")
        ordering = ['order', 'name'] # ترتيب حسب order ثم الاسم

    def __str__(self):
        return self.name

    # def get_absolute_url(self): # قد لا تحتاج لصفحة تفاصيل للشارة نفسها
    #     return reverse('achievements:badge_detail', kwargs={'pk': self.pk})


class UserBadge(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_badges_earned', # اسم أوضح للعلاقة العكسية
        verbose_name=_("المستخدم")
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE, # إذا حُذفت الشارة، يُحذف سجل اكتسابها
        related_name='earned_by_users',
        verbose_name=_("الشارة المكتسبة")
    )
    earned_at = models.DateTimeField(
        auto_now_add=True, # يُضبط تلقائيًا عند الإنشاء
        verbose_name=_("تاريخ الاكتساب")
    )

    class Meta:
        verbose_name = _("شارة مستخدم مكتسبة")
        verbose_name_plural = _("شارات المستخدمين المكتسبة")
        unique_together = ('user', 'badge') # لضمان أن المستخدم يكتسب الشارة مرة واحدة فقط
        ordering = ['-earned_at'] # الأحدث اكتسابًا أولاً
        indexes = [
            models.Index(fields=['user', 'badge']), # فهرس للـ unique_together
            models.Index(fields=['user', '-earned_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"