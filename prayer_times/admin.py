from django.contrib import admin
from .models import Location, PrayerTime, PrayerReminder
from django.utils.translation import gettext_lazy as _

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'country', 'timezone')
    search_fields = ('name', 'country', 'timezone')
    list_filter = ('country', 'timezone')

@admin.register(PrayerTime)
class PrayerTimeAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'prayer_type', 'time', 'is_notified')
    list_filter = ('user', 'date', 'prayer_type', 'is_notified')
    search_fields = ('user__username', 'date')
    date_hierarchy = 'date'
    readonly_fields = ('user', 'date', 'prayer_type', 'time')

@admin.register(PrayerReminder)
class PrayerReminderAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'notification_time_before', 
        'enabled', 
        'daily_werd_reminder_enabled', 
        'daily_werd_reminder_time',
        'is_notified_morning_adhkar_today', # <--- جديد
        'is_notified_evening_adhkar_today', # <--- جديد
        'is_notified_werd_today',           # <--- جديد
        'last_notification_reset_date',     # <--- جديد
    )
    search_fields = ('user__username',)
    list_filter = ('enabled', 'daily_werd_reminder_enabled', 'is_notified_morning_adhkar_today', 'is_notified_evening_adhkar_today', 'is_notified_werd_today')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('إعدادات تذكير الصلوات'), {
            'fields': ('notification_time_before', 'enabled'),
        }),
        (_('إعدادات تذكير الورد اليومي'), {
            'fields': ('daily_werd_reminder_enabled', 'daily_werd_reminder_time'),
        }),
        (_('حالة الإشعارات اليومية'), { # <--- جديد
            'fields': (
                'is_notified_morning_adhkar_today',
                'is_notified_evening_adhkar_today',
                'is_notified_werd_today',
                'last_notification_reset_date',
            ),
            'description': _("هذه الحقول تستخدم لتتبع الإشعارات التي تم إرسالها لهذا اليوم."),
        }),
    )

