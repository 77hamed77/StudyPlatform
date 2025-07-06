import requests
import os
from datetime import datetime, timedelta, time
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.utils import timezone
from django.contrib import messages

from .models import PrayerTime, PrayerReminder, Location
from core.models import Notification
from django.contrib.contenttypes.models import ContentType

class PrayerTimesView(LoginRequiredMixin, View):
    template_name = 'prayer_times/prayer_times.html'

    def get_context_data(self, request, target_date):
        # تحديد الموقع الافتراضي
        location_name = "دمشق" # <--- تم التغيير هنا
        default_latitude = float(os.environ.get('DEFAULT_PRAYER_TIMES_LATITUDE', '33.5104')) # <--- تم التغيير هنا
        default_longitude = float(os.environ.get('DEFAULT_PRAYER_TIMES_LONGITUDE', '36.2784')) # <--- تم التغيير هنا
        default_method = int(os.environ.get('DEFAULT_PRAYER_TIMES_METHOD', '4')) 

        location, created = Location.objects.get_or_create(
            name=location_name,
            defaults={
                'latitude': default_latitude,
                'longitude': default_longitude,
                'country': 'Syria', # <--- تم التغيير هنا
                'timezone': settings.TIME_ZONE,
            }
        )

        # جلب أوقات الصلاة من قاعدة البيانات أو الـ API
        prayer_times_qs = PrayerTime.objects.filter(user=request.user, date=target_date).order_by('time')
        
        if not prayer_times_qs.exists():
            fetched_times = self._fetch_prayer_times_from_api(location, target_date, default_method)
            if fetched_times:
                for prayer_type, prayer_time_str in fetched_times.items():
                    if prayer_time_str:
                        try:
                            prayer_time_obj = datetime.strptime(prayer_time_str, '%H:%M').time()
                            PrayerTime.objects.update_or_create(
                                user=request.user,
                                date=target_date,
                                prayer_type=prayer_type.lower(),
                                defaults={'time': prayer_time_obj, 'is_notified': False}
                            )
                        except ValueError:
                            print(f"Warning: Could not parse time '{prayer_time_str}' for prayer type '{prayer_type}'. Skipping.")
                            continue
                prayer_times_qs = PrayerTime.objects.filter(user=request.user, date=target_date).order_by('time')
            else:
                messages.error(request, _("تعذر جلب أوقات الصلاة. يرجى المحاولة لاحقاً."))
                prayer_times_qs = PrayerTime.objects.none()

        # جلب إعدادات التذكير للمستخدم
        reminder_setting, created = PrayerReminder.objects.get_or_create(user=request.user)

        # التحقق من التذكيرات وإنشاء الإشعارات (فقط لليوم الحالي)
        if target_date == timezone.now().date() and reminder_setting.enabled:
            self._check_and_create_reminders(request.user, prayer_times_qs, reminder_setting.notification_time_before)

        # ترتيب الصلوات للعرض في القالب
        ordered_prayer_types = ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha', 'imsak', 'midnight']
        
        prayer_times_dict = {pt.prayer_type: pt for pt in prayer_times_qs}
        
        display_prayer_times = []
        for p_type in ordered_prayer_types:
            if p_type in prayer_times_dict:
                display_prayer_times.append(prayer_times_dict[p_type])

        return {
            'location': location,
            'prayer_times': display_prayer_times,
            'current_date': target_date,
            'today_date': timezone.now().date(),
            'next_day': target_date + timedelta(days=1),
            'prev_day': target_date - timedelta(days=1),
            'reminder_setting': reminder_setting,
        }

    def get(self, request, *args, **kwargs):
        target_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.now().date()

        context = self.get_context_data(request, target_date)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if 'notification_time_before' in request.POST or 'enable_notifications' in request.POST:
            reminder_setting, created = PrayerReminder.objects.get_or_create(user=request.user)
            
            try:
                minutes_before = int(request.POST.get('notification_time_before', reminder_setting.notification_time_before))
                reminder_setting.notification_time_before = max(0, min(60, minutes_before))
            except ValueError:
                messages.error(request, _("قيمة غير صالحة لدقائق التذكير."))

            enable_notifications = request.POST.get('enable_notifications') == 'on'
            reminder_setting.enabled = enable_notifications
            
            reminder_setting.save()
            messages.success(request, _("تم حفظ إعدادات التذكير بنجاح."))
            
            target_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
            return redirect(f"{request.path}?date={target_date_str}")
        
        return redirect(request.path)

    def _fetch_prayer_times_from_api(self, location, target_date, method):
        api_base_url = settings.ALADHAN_API_BASE_URL
        url = f"{api_base_url}/timings/{target_date.day}-{target_date.month}-{target_date.year}"

        params = {
            'latitude': str(location.latitude),
            'longitude': str(location.longitude),
            'method': method,
            'school': '1',
            'midnightMode': '0',
            'tune': '0,0,0,0,0,0,0,0,0',
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data and data['data'] and data['data']['timings']:
                return data['data']['timings']
            else:
                print(f"Error fetching prayer times: No data or timings found in API response for {target_date}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Aladhan API: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def _check_and_create_reminders(self, user, prayer_times_qs, minutes_before):
        now = timezone.now()
        for prayer in prayer_times_qs:
            prayer_datetime = timezone.make_aware(
                datetime.combine(now.date(), prayer.time),
                timezone.get_current_timezone()
            )

            reminder_time = prayer_datetime - timedelta(minutes=minutes_before)

            if reminder_time <= now < (reminder_time + timedelta(minutes=1)) and not prayer.is_notified and prayer_datetime > now:
                Notification.objects.create(
                    recipient=user,
                    verb=f'{_("تذكير بصلاة")} {prayer.get_prayer_type_display()}',
                    description=f"{_('حان وقت صلاة')} {prayer.get_prayer_type_display()} {_('في')} {prayer.time.strftime('%H:%M')}.",
                    target_content_type=ContentType.objects.get_for_model(prayer),
                    target_object_id=prayer.pk,
                    timestamp=now
                )
                prayer.is_notified = True
                prayer.save(update_fields=['is_notified'])
                print(f"Notification created for {prayer.get_prayer_type_display()} for user {user.username}")

