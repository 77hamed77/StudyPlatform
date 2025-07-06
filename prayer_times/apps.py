from django.apps import AppConfig

class PrayerTimesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prayer_times'

    def ready(self):
        pass  # تعليق الجدولة مؤقتًا
        # from celery import shared_task
        # from celery.schedules import crontab
        # from .tasks import check_prayer_reminders

        # @shared_task
        # def schedule_prayer_reminders():
        #     check_prayer_reminders.delay()
        
        # # جدولة المهمة كل دقيقة (يمكن تعديلها حسب الحاجة)
        # schedule_prayer_reminders.apply_async(schedule=crontab(minute='*/1'))