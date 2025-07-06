from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class PrayerTime(models.Model):
    PRAYER_TYPES = [
        ('fajr', _('الفجر')),
        ('sunrise', _('الشروق')),
        ('dhuhr', _('الظهر')),
        ('asr', _('العصر')),
        ('maghrib', _('المغرب')),
        ('isha', _('العشاء')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prayer_times',
        verbose_name=_("المستخدم")
    )
    prayer_type = models.CharField(
        max_length=10,
        choices=PRAYER_TYPES,
        verbose_name=_("نوع الصلاة")
    )
    time = models.TimeField(
        verbose_name=_("وقت الصلاة")
    )
    date = models.DateField(
        auto_now_add=True,
        verbose_name=_("التاريخ")
    )
    is_notified = models.BooleanField(
        default=False,
        verbose_name=_("تم التذكير")
    )

    class Meta:
        verbose_name = _("وقت صلاة")
        verbose_name_plural = _("أوقات الصلاة")
        unique_together = ('user', 'prayer_type', 'date')
        ordering = ['time']

    def __str__(self):
        return f"{self.prayer_type} - {self.time} ({self.date})"

class PrayerReminder(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prayer_reminders',
        verbose_name=_("المستخدم")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشط")
    )
    notification_time_before = models.PositiveIntegerField(
        default=5,
        verbose_name=_("الوقت قبل الصلاة (بالدقائق)"),
        help_text=_("عدد الدقائق للتذكير قبل الصلاة")
    )

    class Meta:
        verbose_name = _("تذكير صلاة")
        verbose_name_plural = _("تذكيرات الصلاة")

    def __str__(self):
        return f"تذكير لـ {self.user.username} (نشط: {self.is_active})"