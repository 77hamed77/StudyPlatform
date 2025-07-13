from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse # For get_absolute_url if needed
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import JSONField # For storing dashboard preferences as JSON (requires psycopg2)
# If not using PostgreSQL, you might use TextField and serialize/deserialize manually

# Fallback for JSONField if PostgreSQL is not used
try:
    from django.db.models import JSONField
except ImportError:
    # For older Django versions or non-PostgreSQL databases, use TextField and handle JSON manually
    class JSONField(models.TextField):
        def from_db_value(self, value, expression, connection):
            if value is None:
                return value
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {} # Return empty dict on decode error

        def to_python(self, value):
            if isinstance(value, dict) or value is None:
                return value
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}

        def get_prep_value(self, value):
            if value is None:
                return value
            return json.dumps(value)


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
    # Default Pomodoro timer settings for the user
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
    
    # New fields for Dashboard Customization
    # Stores preferences as JSON: {'visible_sections': ['news', 'tasks'], 'section_order': ['tasks', 'news']}
    dashboard_layout_preferences = JSONField(
        default=dict, # Use dict as default for JSONField
        blank=True,
        null=True,
        verbose_name=_("تفضيلات تخطيط لوحة التحكم"),
        help_text=_("تفضيلات المستخدم لعرض وترتيب أقسام لوحة التحكم (JSON).")
    )

    # New field for AI Study Assistant - Study Goals
    study_goals = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("أهداف الدراسة"),
        help_text=_("أهداف الطالب الأكاديمية لمساعد الذكاء الاصطناعي.")
    )

    class Meta:
        verbose_name = _("الملف الشخصي للمستخدم")
        verbose_name_plural = _("الملفات الشخصية للمستخدمين")

    def __str__(self):
        return f"{_('الملف الشخصي لـ')} {self.user.username}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create or update UserProfile when a User object is created or saved.
    """
    if created:
        UserProfile.objects.create(user=instance)
    try:
        instance.profile.save() # Ensure profile is saved if it exists and user is saved
    except UserProfile.DoesNotExist:
        # This condition might not be called if created is true, but it's a safeguard
        UserProfile.objects.create(user=instance)


class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_received',
        verbose_name=_("المستلم")
    )
    # Actor (optional)
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

    # Target (the object the notification relates to)
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

    # New field for AI-driven notifications (e.g., last interaction, importance)
    # This can be used by the AI to decide when to send a reminder
    metadata = JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name=_("بيانات وصفية للإشعار"),
        help_text=_("بيانات إضافية للإشعار (مثل سبب التذكير، تاريخ آخر تفاعل).")
    )

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
    Model for storing educational resources such as courses, links, and sources.
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

    # --- Additional fields for ratings and favorites (not stored directly in the model) ---
    # These properties will be methods to calculate the average from the ratings model
    @property
    def average_rating(self):
        return self.ratings.aggregate(models.Avg('rating'))['rating__avg'] or 0.0

    @property
    def total_ratings(self):
        return self.ratings.count()


# --- New models for Tools and Utilities (from previous update) ---

class DiscussionPost(models.Model):
    """
    Model for a discussion board post.
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
    Model for a comment on a discussion post.
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
        ordering = ['created_at'] # Comments appear in chronological order

    def __str__(self):
        display_name = "مجهول" if self.is_anonymous else self.author.username
        return f"Comment by {display_name} on {self.post.title[:30]}..."


class FAQItem(models.Model):
    """
    Model for a frequently asked question item.
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
    Model for tracking student academic progress (e.g., subject grades).
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
        unique_together = ('user', 'subject', 'date_recorded') # Prevent duplicate grades for the same subject on the same day

    def __str__(self):
        return f"{self.user.username} - {self.subject.name if self.subject else 'N/A'} - Grade: {self.grade}"


# --- New models for Ratings and Favorites ---

class EducationalResourceRating(models.Model):
    """
    Model for rating and reviewing an educational resource by a user.
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
        unique_together = ('resource', 'user') # A user can rate a resource only once
        ordering = ['-created_at']

    def __str__(self):
        return f"تقييم {self.rating} لـ {self.resource.title} بواسطة {self.user.username}"


class UserFavoriteResource(models.Model):
    """
    Model for tracking user's favorite educational resources.
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
        unique_together = ('user', 'resource') # A user can favorite a resource only once
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} فضل {self.resource.title}"

