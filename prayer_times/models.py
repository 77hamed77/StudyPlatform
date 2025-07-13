from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Location(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("الاسم"))
    latitude = models.FloatField(verbose_name=_("خط العرض"))
    longitude = models.FloatField(verbose_name=_("خط الطول"))
    country = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("الدولة"))
    timezone = models.CharField(max_length=255, default='Asia/Damascus', verbose_name=_("المنطقة الزمنية"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("الموقع")
        verbose_name_plural = _("المواقع")


class PrayerTime(models.Model):
    PRAYER_CHOICES = [
        ('fajr', _('الفجر')),
        ('sunrise', _('الشروق')),
        ('dhuhr', _('الظهر')),
        ('asr', _('العصر')),
        ('maghrib', _('المغرب')),
        ('isha', _('العشاء')),
        ('imsak', _('الإمساك')),
        ('midnight', _('منتصف الليل')),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prayer_times', verbose_name=_("المستخدم"))
    date = models.DateField(verbose_name=_("التاريخ"))
    prayer_type = models.CharField(max_length=20, choices=PRAYER_CHOICES, verbose_name=_("نوع الصلاة"))
    time = models.TimeField(verbose_name=_("الوقت"))
    is_notified = models.BooleanField(default=False, verbose_name=_("تم الإشعار"))

    class Meta:
        unique_together = ('user', 'date', 'prayer_type')
        verbose_name = _("وقت الصلاة")
        verbose_name_plural = _("أوقات الصلاة")
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.user.username} - {self.get_prayer_type_display()} on {self.date} at {self.time}"

class PrayerReminder(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='prayer_reminder_setting', verbose_name=_("المستخدم"))
    enabled = models.BooleanField(default=True, verbose_name=_("تمكين الإشعارات"))
    notification_time_before = models.IntegerField(default=10, verbose_name=_("وقت الإشعار قبل (بالدقائق)")) # دقائق قبل الأذان

    # حقول لتتبع إشعارات الأذكار والورد اليومي
    daily_werd_reminder_enabled = models.BooleanField(default=False, verbose_name=_("تمكين تذكير الورد اليومي"))
    daily_werd_reminder_time = models.TimeField(blank=True, null=True, verbose_name=_("وقت تذكير الورد اليومي"))
    
    is_notified_morning_adhkar_today = models.BooleanField(default=False, verbose_name=_("تم إشعار أذكار الصباح اليوم"))
    is_notified_evening_adhkar_today = models.BooleanField(default=False, verbose_name=_("تم إشعار أذكار المساء اليوم"))
    is_notified_werd_today = models.BooleanField(default=False, verbose_name=_("تم إشعار الورد اليومي اليوم"))
    last_notification_reset_date = models.DateField(default=timezone.now, verbose_name=_("تاريخ آخر إعادة تعيين للإشعارات"))

    class Meta:
        verbose_name = _("إعدادات تذكير الصلاة")
        verbose_name_plural = _("إعدادات تذكيرات الصلاة")

    def __str__(self):
        return f"إعدادات تذكير لـ {self.user.username}"


# النموذج الجديد للعناصر المفضلة
class FavoriteItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_items', verbose_name=_("المستخدم"))
    
    # Generic Foreign Key to link to different content types (Adhkar, Dua, Hadith)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_("نوع المحتوى"))
    object_id = models.CharField(max_length=255, verbose_name=_("معرف العنصر")) # استخدام CharField لدعم IDs من JSON (قد تكون أرقام أو سلاسل)
    
    # حقول إضافية لتخزين البيانات مباشرة لتجنب إعادة قراءة JSON
    item_text = models.TextField(verbose_name=_("نص العنصر"))
    item_category = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("تصنيف العنصر"))
    item_type = models.CharField(max_length=50, verbose_name=_("نوع العنصر")) # 'adhkar', 'dua', 'hadith'

    # لضمان عدم تكرار نفس العنصر المفضل لنفس المستخدم
    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        verbose_name = _("عنصر مفضل")
        verbose_name_plural = _("عناصر مفضلة")
        ordering = ['user', 'item_type', 'item_category']

    def __str__(self):
        return f"{self.user.username}'s Favorite: {self.item_type} - {self.item_text[:50]}..."

