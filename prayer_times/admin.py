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
    date_hierarchy = 'date' # لتمكين التنقل حسب التاريخ
    readonly_fields = ('user', 'date', 'prayer_type', 'time') # لا تسمح بتعديل هذه الحقول يدوياً

@admin.register(PrayerReminder)
class PrayerReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_time_before', 'enabled')
    search_fields = ('user__username',)
    list_filter = ('enabled',)
    raw_id_fields = ('user',) # لتحسين أداء البحث عن المستخدمين

