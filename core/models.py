from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse # لاستخدامه في get_absolute_url إذا لزم الأمر
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
        verbose_name=_("المستخدم")
    )
    dark_mode_enabled = models.BooleanField(
        default=False,
        verbose_name=_("تفعيل الوضع الليلي")
    )
    # إعدادات مؤقت بومودورو الافتراضية للمستخدم
    pomodoro_work_duration = models.PositiveIntegerField(
        default=25,
        verbose_name=_("مدة جلسة العمل (دقائق)"),
        help_text=_("القيمة الافتراضية هي 25 دقيقة. (من 1 إلى 120)")
    )
    pomodoro_short_break_duration = models.PositiveIntegerField(
        default=5,
        verbose_name=_("مدة الراحة القصيرة (دقائق)"),
        help_text=_("القيمة الافتراضية هي 5 دقائق. (من 1 إلى 60)")
    )
    pomodoro_long_break_duration = models.PositiveIntegerField(
        default=15,
        verbose_name=_("مدة الراحة الطويلة (دقائق)"),
        help_text=_("القيمة الافتراضية هي 15 دقيقة. (من 1 إلى 90)")
    )
    pomodoro_sessions_before_long_break = models.PositiveIntegerField(
        default=4,
        verbose_name=_("عدد جلسات العمل قبل الراحة الطويلة"),
        help_text=_("القيمة الافتراضية هي 4 جلسات. (من 1 إلى 10)")
    )
    
    class Meta:
        verbose_name = _("الملف الشخصي للمستخدم")
        verbose_name_plural = _("الملفات الشخصية للمستخدمين")

    def __str__(self):
        return f"{_('الملف الشخصي لـ')} {self.user.username}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    إشارة لإنشاء أو تحديث UserProfile تلقائيًا عند إنشاء أو حفظ كائن User.
    """
    if created:
        UserProfile.objects.create(user=instance)
    try:
        instance.profile.save() # التأكد من حفظ البروفايل إذا كان موجودًا وتم حفظ المستخدم
    except UserProfile.DoesNotExist:
        # هذا الشرط قد لا يُستدعى إذا كان created صحيحًا، لكنه كاحتياط
        UserProfile.objects.create(user=instance)


class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_received',
        verbose_name=_("المستلم")
    )
    # الفاعل (اختياري)
    actor_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='actor_notifications_%(app_label)s_%(class)s_related',
        null=True, blank=True
    )
    actor_object_id = models.PositiveIntegerField(null=True, blank=True)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255, verbose_name=_("الفعل"))
    description = models.TextField(blank=True, null=True, verbose_name=_("الوصف التفصيلي للإشعار"))

    # الهدف (الكائن الذي يتعلق به الإشعار)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='target_notifications_%(app_label)s_%(class)s_related',
        null=True, blank=True
    )
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    unread = models.BooleanField(default=True, db_index=True, verbose_name=_("غير مقروء"))
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, verbose_name=_("التوقيت"))

    class Meta:
        ordering = ('-timestamp',)
        verbose_name = _("إشعار")
        verbose_name_plural = _("إشعارات")
        indexes = [
            models.Index(fields=['recipient', 'unread']),
        ]

    def __str__(self):
        if self.target:
            return f"{self.actor if self.actor else _('النظام')} {self.verb} {self.target}"
        elif self.actor:
            return f"{self.actor} {self.verb}"
        return f"{self.verb} ({_('إشعار نظام')})"

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save(update_fields=['unread'])

    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.save(update_fields=['unread'])

    def get_absolute_url(self):
        if self.target and hasattr(self.target, 'get_absolute_url'):
            return self.target.get_absolute_url()
        return reverse('core:notifications_list')


class DailyQuote(models.Model):
    quote_text = models.TextField(verbose_name=_("نص الاقتباس/النصيحة"))
    author_or_source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("الكاتب/المصدر")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("نشط (يمكن عرضه)")
    )

    class Meta:
        verbose_name = _("اقتباس/نصيحة يومية")
        verbose_name_plural = _("اقتباسات/نصائح يومية")
        ordering = ['-id']

    def __str__(self):
        return self.quote_text[:70] + "..." if len(self.quote_text) > 70 else self.quote_text


class EducationalResource(models.Model):
    """
    نموذج لتخزين الموارد التعليمية مثل الكورسات، الروابط، والمصادر.
    """
    title = models.CharField(max_length=255, verbose_name="عنوان المورد")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    link = models.URLField(verbose_name="الرابط")
    is_active = models.BooleanField(default=True, verbose_name="نشط (للعرض العام)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مورد تعليمي"
        verbose_name_plural = "الموارد التعليمية"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    # --- حقول إضافية للتقييمات والمفضلة (غير مخزنة في النموذج مباشرة) ---
    # هذه الخصائص ستكون طرقًا لحساب المتوسط من نموذج التقييمات
    @property
    def average_rating(self):
        return self.ratings.aggregate(models.Avg('rating'))['rating__avg'] or 0.0

    @property
    def total_ratings(self):
        return self.ratings.count()


# --- نماذج جديدة للأدوات والمرافق (من التحديث السابق) ---

class DiscussionPost(models.Model):
    """
    نموذج لمنشور في لوحة المناقشات.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_posts', verbose_name=_("الكاتب"))
    title = models.CharField(max_length=255, verbose_name=_("العنوان"))
    content = models.TextField(verbose_name=_("المحتوى"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))
    is_anonymous = models.BooleanField(default=False, verbose_name=_("نشر كمجهول"), help_text=_("إذا تم تحديده، سيتم إخفاء اسم المستخدم."))

    class Meta:
        verbose_name = _("منشور مناقشة")
        verbose_name_plural = _("منشورات المناقشة")
        ordering = ['-created_at']

    def __str__(self):
        display_name = "مجهول" if self.is_anonymous else self.author.username
        return f"{self.title} by {display_name}"

    def get_absolute_url(self):
        return reverse('core:discussion_post_detail', kwargs={'pk': self.pk})


class DiscussionComment(models.Model):
    """
    نموذج لتعليق على منشور في لوحة المناقشات.
    """
    post = models.ForeignKey(DiscussionPost, on_delete=models.CASCADE, related_name='comments', verbose_name=_("المنشور"))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_comments', verbose_name=_("الكاتب"))
    content = models.TextField(verbose_name=_("التعليق"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))
    is_anonymous = models.BooleanField(default=False, verbose_name=_("نشر كمجهول"), help_text=_("إذا تم تحديده، سيتم إخفاء اسم المستخدم."))

    class Meta:
        verbose_name = _("تعليق مناقشة")
        verbose_name_plural = _("تعليقات المناقشة")
        ordering = ['created_at'] # التعليقات تظهر بترتيب زمني تصاعدي

    def __str__(self):
        display_name = "مجهول" if self.is_anonymous else self.author.username
        return f"Comment by {display_name} on {self.post.title[:30]}..."


class FAQItem(models.Model):
    """
    نموذج لعنصر سؤال شائع.
    """
    question = models.CharField(max_length=255, verbose_name=_("السؤال"))
    answer = models.TextField(verbose_name=_("الإجابة"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتيب العرض"), help_text=_("رقم لترتيب الأسئلة الشائعة."))
    is_active = models.BooleanField(default=True, verbose_name=_("نشط (للعرض العام)"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإنشاء"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))

    class Meta:
        verbose_name = _("سؤال شائع")
        verbose_name_plural = _("الأسئلة الشائعة")
        ordering = ['order', 'question']

    def __str__(self):
        return self.question


class AcademicProgress(models.Model):
    """
    نموذج لتتبع التقدم الأكاديمي للطالب (مثل درجات المواد).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academic_progress', verbose_name=_("المستخدم"))
    subject = models.ForeignKey('files_manager.Subject', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("المادة الدراسية"))
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("الدرجة"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات"))
    date_recorded = models.DateField(default=timezone.now, verbose_name=_("تاريخ التسجيل"))

    class Meta:
        verbose_name = _("تقدم أكاديمي")
        verbose_name_plural = _("التقدم الأكاديمي")
        ordering = ['-date_recorded', 'subject__name']
        unique_together = ('user', 'subject', 'date_recorded') # لمنع تكرار الدرجات لنفس المادة في نفس اليوم

    def __str__(self):
        return f"{self.user.username} - {self.subject.name if self.subject else 'N/A'} - Grade: {self.grade}"


# --- نماذج جديدة للتقييمات والمفضلة ---

class EducationalResourceRating(models.Model):
    """
    نموذج لتقييم ومراجعة مورد تعليمي بواسطة مستخدم.
    """
    resource = models.ForeignKey(
        EducationalResource,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name=_("المورد التعليمي")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resource_ratings',
        verbose_name=_("المستخدم")
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("التقييم (من 1 إلى 5)")
    )
    review_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("نص المراجعة")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ التقييم"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاريخ التحديث"))

    class Meta:
        verbose_name = _("تقييم مورد تعليمي")
        verbose_name_plural = _("تقييمات الموارد التعليمية")
        unique_together = ('resource', 'user') # المستخدم يمكنه تقييم مورد واحد مرة واحدة فقط
        ordering = ['-created_at']

    def __str__(self):
        return f"تقييم {self.rating} لـ {self.resource.title} بواسطة {self.user.username}"


class UserFavoriteResource(models.Model):
    """
    نموذج لتتبع الموارد التعليمية المفضلة للمستخدم.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_resources',
        verbose_name=_("المستخدم")
    )
    resource = models.ForeignKey(
        EducationalResource,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_("المورد التعليمي")
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الإضافة للمفضلة"))

    class Meta:
        verbose_name = _("مورد تعليمي مفضل")
        verbose_name_plural = _("الموارد التعليمية المفضلة")
        unique_together = ('user', 'resource') # المستخدم يمكنه تفضيل مورد واحد مرة واحدة فقط
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} فضل {self.resource.title}"

