from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import PrayerTime, PrayerReminder
from core.models import Notification
from django.contrib.contenttypes.models import ContentType

@shared_task
def check_prayer_reminders():
    now = timezone.now()
    for reminder in PrayerReminder.objects.filter(is_active=True).select_related('user'):
        prayer_times = PrayerTime.objects.filter(
            user=reminder.user,
            date=now.date(),
            is_notified=False
        ).select_related('user')
        for prayer in prayer_times:
            reminder_time = now.replace(
                hour=prayer.time.hour,
                minute=prayer.time.minute,
                second=0,
                microsecond=0
            ) - timedelta(minutes=reminder.notification_time_before)
            # توسيع نافذة التحقق إلى 5 دقائق
            time_diff = abs((reminder_time - now).total_seconds()) / 60
            if 0 <= time_diff <= 5:  # تحقق خلال 5 دقائق
                try:
                    prayer_type_display = prayer.get_prayer_type_display()
                except AttributeError:
                    prayer_type_display = str(prayer.prayer_type)  # بديل إذا لم يكن هناك CHOICES
                notification = Notification(
                    recipient=reminder.user,
                    verb=f'تذكير بصلاة {prayer_type_display}',
                    description=f"حان وقت صلاة {prayer_type_display} في {prayer.time.strftime('%H:%M')}",
                    target=prayer,
                    timestamp=now
                )
                notification.save()
                prayer.is_notified = True
                prayer.save()