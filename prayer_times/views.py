import requests
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import PrayerTime, PrayerReminder
from datetime import datetime, timedelta
from core.models import Notification

class PrayerTimesView(LoginRequiredMixin, TemplateView):
    template_name = 'prayer_times/prayer_times.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        prayer_times = PrayerTime.objects.filter(user=self.request.user, date=today).order_by('time')
        if not prayer_times.exists():
            prayer_times = self.fetch_prayer_times()
            for prayer in prayer_times:
                PrayerTime.objects.update_or_create(
                    user=self.request.user,
                    prayer_type=prayer['type'],
                    date=today,
                    defaults={'time': prayer['time']}
                )
            prayer_times = PrayerTime.objects.filter(user=self.request.user, date=today).order_by('time')

        reminder = PrayerReminder.objects.filter(user=self.request.user).first()
        if reminder:
            self.check_and_create_reminders(prayer_times, reminder.notification_time_before)

        context['prayer_times'] = prayer_times
        context['reminder'] = reminder
        return context

    def fetch_prayer_times(self):
        api_url = 'https://api.aladhan.com/v1/timingsByCity?city=Riyadh&country=Saudi%20Arabia&method=4'
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()['data']['timings']
            return [
                {'type': 'fajr', 'time': datetime.strptime(data['Fajr'], '%H:%M').time()},
                {'type': 'sunrise', 'time': datetime.strptime(data['Sunrise'], '%H:%M').time()},
                {'type': 'dhuhr', 'time': datetime.strptime(data['Dhuhr'], '%H:%M').time()},
                {'type': 'asr', 'time': datetime.strptime(data['Asr'], '%H:%M').time()},
                {'type': 'maghrib', 'time': datetime.strptime(data['Maghrib'], '%H:%M').time()},
                {'type': 'isha', 'time': datetime.strptime(data['Isha'], '%H:%M').time()},
            ]
        return []

    def check_and_create_reminders(self, prayer_times, minutes_before):
        now = timezone.now()
        for prayer in prayer_times:
            reminder_time = now.replace(hour=prayer.time.hour, minute=prayer.time.minute, second=0, microsecond=0) - timedelta(minutes=minutes_before)
            if abs((reminder_time - now).total_seconds()) < 300:  # تحقق خلال 5 دقائق
                if not prayer.is_notified:
                    self.create_notification(prayer, reminder_time)

    def create_notification(self, prayer, reminder_time):
        notification = Notification(
            recipient=self.request.user,
            verb=f'تذكير بصلاة {prayer.get_prayer_type_display()}',
            description=f"حان وقت صلاة {prayer.get_prayer_type_display()} في {reminder_time.strftime('%H:%M')}",
            target=prayer,
            timestamp=reminder_time
        )
        notification.save()
        prayer.is_notified = True
        prayer.save()

    def post(self, request, *args, **kwargs):
        reminder, created = PrayerReminder.objects.get_or_create(user=request.user)
        if 'notification_time_before' in request.POST:
            reminder.notification_time_before = int(request.POST['notification_time_before'])
            reminder.save()
        return self.get(request, *args, **kwargs)