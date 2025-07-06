from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model() # للحصول على نموذج المستخدم الحالي

class Location(models.Model):
    """
    نموذج لتخزين معلومات الموقع (المدينة) لأوقات الصلاة.
    يمكن أن يكون لديك مواقع متعددة إذا كنت تدعم مدن مختلفة.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name=_("اسم المدينة"))
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name=_("خط العرض"))
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name=_("خط الطول"))
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("البلد"))
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("الولاية/المقاطعة"))
    timezone = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("المنطقة الزمنية (IANA)")) # مثال: Asia/Riyadh

    class Meta:
        verbose_name = _("موقع الصلاة")
        verbose_name_plural = _("مواقع الصلاة")
        ordering = ['name']

    def __str__(self):
        return self.name

class PrayerTime(models.Model):
    """
    نموذج لتخزين أوقات الصلاة اليومية لكل مستخدم.
    يستخدم للتخزين المؤقت (caching) لتجنب استدعاء API بشكل متكرر.
    """
    PRAYER_CHOICES = [
        ('fajr', _('الفجر')),
        ('sunrise', _('الشروق')),
        ('dhuhr', _('الظهر')),
        ('asr', _('العصر')),
        ('maghrib', _('المغرب')),
        ('isha', _('العشاء')),
        # يمكنك إضافة المزيد إذا كان الـ API يوفرها وتريد تخزينها
        ('imsak', _('الإمساك')),
        ('midnight', _('منتصف الليل')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prayer_times_set', verbose_name=_("المستخدم"))
    date = models.DateField(verbose_name=_("التاريخ"))
    prayer_type = models.CharField(max_length=10, choices=PRAYER_CHOICES, verbose_name=_("نوع الصلاة"))
    time = models.TimeField(verbose_name=_("الوقت"))
    is_notified = models.BooleanField(default=False, verbose_name=_("تم التذكير")) # لتتبع ما إذا تم إرسال إشعار

    class Meta:
        verbose_name = _("وقت صلاة")
        verbose_name_plural = _("أوقات الصلاة")
        unique_together = ('user', 'date', 'prayer_type') # كل صلاة فريدة لكل مستخدم وتاريخ
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.get_prayer_type_display()} - {self.time.strftime('%H:%M')} ({self.date})"

class PrayerReminder(models.Model):
    """
    نموذج لتخزين إعدادات التذكير بالصلاة لكل مستخدم.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='prayer_reminder_settings', verbose_name=_("المستخدم"))
    notification_time_before = models.PositiveIntegerField(
        default=5,
        verbose_name=_("التذكير قبل الصلاة (بالدقائق)"),
        help_text=_("عدد الدقائق قبل وقت الصلاة لإرسال التذكير.")
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_("تفعيل التذكيرات الصوتية"),
        help_text=_("تفعيل هذا الخيار سيسمح بتشغيل صوت الأذان عند وقت الصلاة.")
    )

    class Meta:
        verbose_name = _("إعداد تذكير الصلاة")
        verbose_name_plural = _("إعدادات تذكير الصلاة")

    def __str__(self):
        return f"{_('إعدادات تذكير صلاة')} {self.user.username}"

