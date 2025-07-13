from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction # For atomic updates
from django.utils import timezone # تم إضافة هذا الاستيراد لـ timezone.now()

# تم تغيير هذا الاستيراد:
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey # تم إضافة هذا الاستيراد لـ GenericForeignKey

# Assuming Subject model is available from files_manager app
try:
    from files_manager.models import Subject
except ImportError:
    # Fallback if files_manager.models.Subject is not found
    class Subject(models.Model):
        name = models.CharField(max_length=255, unique=True, verbose_name="اسم المادة (Placeholder)")
        def __str__(self):
            return self.name
    print("Warning: files_manager.models.Subject not found. Using a placeholder Subject model in achievements app.")

# --- Existing Badge Models ---

class Badge(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("اسم الشارة")
    )
    description = models.TextField(verbose_name=_("وصف الشارة"))
    icon_class = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("فئة CSS للأيقونة (Font Awesome)"),
        help_text=_("مثال: fas fa-star, mdi mdi-trophy. اترك فارغًا إذا استخدمت صورة.")
    )
    icon_image = models.ImageField(
        upload_to='badges_icons/',
        blank=True,
        null=True,
        verbose_name=_("صورة أيقونة الشارة (اختياري)")
    )
    criteria_description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("وصف معيار تحقيق الشارة")
    )
    badge_type_key = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text=_("مفتاح برمجي فريد لنوع الشارة (مثل TASK_COMPLETER_10).")
    )
    order = models.PositiveIntegerField(default=0, db_index=True, help_text=_("لتحديد ترتيب ظهور الشارات."))

    class Meta:
        verbose_name = _("شارة")
        verbose_name_plural = _("شارات")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_badges_earned',
        verbose_name=_("المستخدم")
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='earned_by_users',
        verbose_name=_("الشارة المكتسبة")
    )
    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("تاريخ الاكتساب")
    )

    class Meta:
        verbose_name = _("شارة مستخدم مكتسبة")
        verbose_name_plural = _("شارات المستخدمين المكتسبة")
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'badge']),
            models.Index(fields=['user', '-earned_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"

# --- New Gamification Models ---

class UserAchievementStats(models.Model):
    """
    يخزن نقاط الخبرة (XP) والمستوى الحالي لكل مستخدم.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='achievement_stats',
        verbose_name=_("المستخدم")
    )
    total_xp = models.PositiveIntegerField(default=0, verbose_name=_("إجمالي نقاط الخبرة"))
    level = models.PositiveIntegerField(default=1, verbose_name=_("المستوى الحالي"))
    last_xp_update = models.DateTimeField(auto_now=True, verbose_name=_("آخر تحديث لنقاط الخبرة"))

    class Meta:
        verbose_name = _("إحصائيات إنجازات المستخدم")
        verbose_name_plural = _("إحصائيات إنجازات المستخدمين")
        ordering = ['-total_xp'] # لسهولة بناء لوحة الصدارة

    def __str__(self):
        return f"إحصائيات {self.user.username}: المستوى {self.level}, نقاط الخبرة {self.total_xp}"

    def add_xp(self, amount):
        """
        يضيف نقاط خبرة ويحدث المستوى إذا لزم الأمر.
        """
        if amount <= 0:
            return

        self.total_xp += amount
        # منطق تحديد المستوى (يمكن تعديله ليكون أكثر تعقيدًا)
        # مثال بسيط: كل 1000 نقطة خبرة = مستوى جديد
        # يمكن استخدام دالة أسية أو جدول مستويات محدد
        new_level = (self.total_xp // 1000) + 1
        if new_level > self.level:
            self.level = new_level
            # يمكن هنا إرسال إشارة أو إنشاء إشعار لرفع المستوى
            # (سيتم التعامل معها في signals.py)
        self.save(update_fields=['total_xp', 'level', 'last_xp_update'])


@receiver(post_save, sender=User)
def create_user_achievement_stats(sender, instance, created, **kwargs):
    """
    ينشئ UserAchievementStats لكل مستخدم جديد.
    """
    if created:
        UserAchievementStats.objects.create(user=instance)


class XPTransaction(models.Model):
    """
    يسجل كل عملية اكتساب نقاط خبرة (XP).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='xp_transactions',
        verbose_name=_("المستخدم")
    )
    amount = models.IntegerField(verbose_name=_("مقدار نقاط الخبرة"))
    activity = models.CharField(max_length=255, verbose_name=_("النشاط")) # e.g., 'Task Completed', 'File Read', 'Post Created'
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("الوقت"))
    
    # Optional: Generic foreign key to link to the specific object that granted XP
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _("عملية نقاط الخبرة")
        verbose_name_plural = _("عمليات نقاط الخبرة")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} اكتسب {self.amount} XP من {self.activity}"


class StudyChallenge(models.Model):
    """
    يعرف تحديًا دراسيًا يمكن للطلاب المشاركة فيه.
    """
    CHALLENGE_TYPE_CHOICES = (
        ('tasks_completed', 'إكمال عدد من المهام'),
        ('files_read', 'قراءة عدد من الملفات'),
        ('pomodoro_sessions', 'إكمال جلسات بومودورو'),
        ('forum_posts', 'المساهمة بمنشورات في المنتدى'),
        ('group_messages', 'إرسال رسائل في المجموعات'),
        ('custom', 'تحدي مخصص'),
    )

    name = models.CharField(max_length=255, verbose_name=_("اسم التحدي"))
    description = models.TextField(verbose_name=_("وصف التحدي"))
    challenge_type = models.CharField(
        max_length=50,
        choices=CHALLENGE_TYPE_CHOICES,
        verbose_name=_("نوع التحدي")
    )
    target_value = models.PositiveIntegerField(
        verbose_name=_("القيمة المستهدفة"),
        help_text=_("مثال: 10 مهام، 5 ملفات، 3 جلسات بومودورو")
    )
    xp_reward = models.PositiveIntegerField(default=0, verbose_name=_("مكافأة نقاط الخبرة"))
    badge_reward = models.ForeignKey(
        Badge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("شارة المكافأة")
    )
    start_date = models.DateTimeField(verbose_name=_("تاريخ البدء"))
    end_date = models.DateTimeField(verbose_name=_("تاريخ الانتهاء"))
    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))

    class Meta:
        verbose_name = _("تحدي دراسي")
        verbose_name_plural = _("تحديات دراسية")
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def is_current(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def is_upcoming(self):
        now = timezone.now()
        return now < self.start_date

    @property
    def is_past(self):
        now = timezone.now()
        return now > self.end_date


class UserStudyChallenge(models.Model):
    """
    يتتبع تقدم المستخدم في تحدي دراسي معين.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_challenges',
        verbose_name=_("المستخدم")
    )
    challenge = models.ForeignKey(
        StudyChallenge,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_("التحدي")
    )
    current_progress = models.PositiveIntegerField(default=0, verbose_name=_("التقدم الحالي"))
    completed = models.BooleanField(default=False, verbose_name=_("اكتمل"))
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاريخ الانضمام"))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("تاريخ الإكمال"))

    class Meta:
        unique_together = ('user', 'challenge') # المستخدم يمكنه الانضمام إلى التحدي مرة واحدة فقط
        verbose_name = _("تحدي مستخدم دراسي")
        verbose_name_plural = _("تحديات المستخدمين الدراسية")
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.challenge.name} ({'مكتمل' if self.completed else 'قيد التقدم'})"

    def update_progress(self, amount=1):
        """
        يحدث تقدم المستخدم في التحدي.
        """
        if self.completed:
            return False # لا يمكن تحديث تحدي مكتمل

        self.current_progress += amount
        if self.current_progress >= self.challenge.target_value:
            self.current_progress = self.challenge.target_value # لا يتجاوز الهدف
            self.completed = True
            self.completed_at = timezone.now()
            self.save(update_fields=['current_progress', 'completed', 'completed_at'])
            
            # منح المكافآت عند الإكمال (سيتم التعامل معها في signals.py)
            return True # تم الإكمال
        else:
            self.save(update_fields=['current_progress'])
            return False # لم يكتمل بعد
