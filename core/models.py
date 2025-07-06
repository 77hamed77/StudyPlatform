from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse # لاستخدامه في get_absolute_url إذا لزم الأمر

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
    
    # --- حقول إعدادات التذكير بالصلاة (جديد) ---
    # لقد قمت بتعريف PrayerReminder كنموذج منفصل، لذا لا حاجة لهذه الحقول هنا.
    # ولكن إذا كنت تفضل دمجها في UserProfile، فهذا هو المكان المناسب.
    # بما أنك قدمت PrayerReminder في الـ views، سأفترض أنك تريد الاحتفاظ به منفصلاً.
    # إذا غيرت رأيك وأردت دمجها، أخبرني.
    # prayer_reminder_enabled = models.BooleanField(default=True, verbose_name=_("تفعيل تذكيرات الصلاة"))
    # prayer_reminder_minutes_before = models.IntegerField(default=5, verbose_name=_("التذكير قبل الصلاة (دقائق)"))
    # -------------------------------------------

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

