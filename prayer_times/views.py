import requests
import os
from datetime import datetime, timedelta, time
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse

from .models import PrayerTime, PrayerReminder, Location
from core.models import Notification
from django.contrib.contenttypes.models import ContentType

class PrayerTimesView(LoginRequiredMixin, View):
    template_name = 'prayer_times/prayer_times.html'

    def get_context_data(self, request, target_date):
        location_name = "دمشق" # اسم المدينة الافتراضي
        default_latitude = float(os.environ.get('DEFAULT_PRAYER_TIMES_LATITUDE', '33.5104'))
        default_longitude = float(os.environ.get('DEFAULT_PRAYER_TIMES_LONGITUDE', '36.2784'))
        default_method = int(os.environ.get('DEFAULT_PRAYER_TIMES_METHOD', '4')) 

        location, created = Location.objects.get_or_create(
            name=location_name,
            defaults={
                'latitude': default_latitude,
                'longitude': default_longitude,
                'country': 'Syria',
                'timezone': settings.TIME_ZONE,
            }
        )

        prayer_times_qs = PrayerTime.objects.filter(user=request.user, date=target_date).order_by('time')
        
        if not prayer_times_qs.exists():
            fetched_times = self._fetch_prayer_times_from_api(location, target_date, default_method)
            if fetched_times:
                for prayer_type, prayer_time_str in fetched_times.items():
                    if prayer_time_str:
                        try:
                            prayer_time_obj = datetime.strptime(prayer_time_str, '%H:%M').time()
                            if prayer_type.lower() in [choice[0] for choice in PrayerTime.PRAYER_CHOICES]:
                                PrayerTime.objects.update_or_create(
                                    user=request.user,
                                    date=target_date,
                                    prayer_type=prayer_type.lower(),
                                    defaults={'time': prayer_time_obj, 'is_notified': False}
                                )
                            else:
                                print(f"Warning: Prayer type '{prayer_type}' not in PRAYER_CHOICES. Skipping.")
                        except ValueError:
                            print(f"Warning: Could not parse time '{prayer_time_str}' for prayer type '{prayer_type}'. Skipping.")
                            continue
                prayer_times_qs = PrayerTime.objects.filter(user=request.user, date=target_date).order_by('time')
            else:
                messages.error(request, _("تعذر جلب أوقات الصلاة. يرجى المحاولة لاحقاً."))
                prayer_times_qs = PrayerTime.objects.none()

        reminder_setting, created = PrayerReminder.objects.get_or_create(user=request.user)

        if target_date == timezone.now().date():
            self._check_and_create_reminders(request.user, prayer_times_qs, reminder_setting)

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
        if 'notification_time_before' in request.POST or 'enable_notifications' in request.POST or \
           'daily_werd_reminder_enabled' in request.POST or 'daily_werd_reminder_time' in request.POST:
            
            reminder_setting, created = PrayerReminder.objects.get_or_create(user=request.user)
            
            try:
                minutes_before = int(request.POST.get('notification_time_before', reminder_setting.notification_time_before))
                reminder_setting.notification_time_before = max(0, min(60, minutes_before))
            except ValueError:
                messages.error(request, _("قيمة غير صالحة لدقائق التذكير."))

            reminder_setting.enabled = request.POST.get('enable_notifications') == 'on'
            
            reminder_setting.daily_werd_reminder_enabled = request.POST.get('daily_werd_reminder_enabled') == 'on'
            werd_time_str = request.POST.get('daily_werd_reminder_time')
            if werd_time_str:
                try:
                    werd_time_obj = datetime.strptime(werd_time_str, '%H:%M').time()
                    reminder_setting.daily_werd_reminder_time = werd_time_obj
                except ValueError:
                    messages.error(request, _("تنسيق وقت الورد اليومي غير صالح. استخدم HH:MM."))

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

    def _check_and_create_reminders(self, user, prayer_times_qs, reminder_setting):
        now = timezone.now()
        today_date = now.date()

        # --- تذكيرات الصلوات العادية ---
        if reminder_setting.enabled:
            for prayer in prayer_times_qs:
                prayer_datetime = timezone.make_aware(
                    datetime.combine(today_date, prayer.time),
                    timezone.get_current_timezone()
                )
                reminder_time = prayer_datetime - timedelta(minutes=reminder_setting.notification_time_before)

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

        # --- تذكير أذكار الصباح والمساء والورد اليومي ---
        fajr_time_obj = PrayerTime.objects.filter(user=user, date=today_date, prayer_type='fajr').first()
        asr_time_obj = PrayerTime.objects.filter(user=user, date=today_date, prayer_type='asr').first()

        # تذكير أذكار الصباح (بعد الفجر بـ 15 دقيقة)
        if fajr_time_obj and fajr_time_obj.time:
            morning_adhkar_reminder_datetime = timezone.make_aware(
                datetime.combine(today_date, fajr_time_obj.time),
                timezone.get_current_timezone()
            ) + timedelta(minutes=15)

            if morning_adhkar_reminder_datetime <= now < (morning_adhkar_reminder_datetime + timedelta(minutes=1)) and not reminder_setting.is_notified_morning_adhkar_today:
                Notification.objects.create(
                    recipient=user,
                    verb=_("تذكير أذكار الصباح"),
                    description=_("حان وقت قراءة أذكار الصباح."),
                    timestamp=now,
                    target_content_type=ContentType.objects.get_for_model(PrayerReminder),
                    target_object_id=reminder_setting.pk,
                )
                reminder_setting.is_notified_morning_adhkar_today = True
                reminder_setting.save(update_fields=['is_notified_morning_adhkar_today'])
                print(f"Notification created for Morning Adhkar for user {user.username}")

        # تذكير أذكار المساء (بعد العصر بـ 15 دقيقة)
        if asr_time_obj and asr_time_obj.time:
            evening_adhkar_reminder_datetime = timezone.make_aware(
                datetime.combine(today_date, asr_time_obj.time),
                timezone.get_current_timezone()
            ) + timedelta(minutes=15)

            if evening_adhkar_reminder_datetime <= now < (evening_adhkar_reminder_datetime + timedelta(minutes=1)) and not reminder_setting.is_notified_evening_adhkar_today:
                Notification.objects.create(
                    recipient=user,
                    verb=_("تذكير أذكار المساء"),
                    description=_("حان وقت قراءة أذكار المساء."),
                    timestamp=now,
                    target_content_type=ContentType.objects.get_for_model(PrayerReminder),
                    target_object_id=reminder_setting.pk,
                )
                reminder_setting.is_notified_evening_adhkar_today = True
                reminder_setting.save(update_fields=['is_notified_evening_adhkar_today'])
                print(f"Notification created for Evening Adhkar for user {user.username}")

        # تذكير الورد اليومي (في وقت محدد يختاره المستخدم)
        if reminder_setting.daily_werd_reminder_enabled and reminder_setting.daily_werd_reminder_time:
            werd_reminder_datetime = timezone.make_aware(
                datetime.combine(today_date, reminder_setting.daily_werd_reminder_time),
                timezone.get_current_timezone()
            )

            if werd_reminder_datetime <= now < (werd_reminder_datetime + timedelta(minutes=1)) and not reminder_setting.is_notified_werd_today:
                Notification.objects.create(
                    recipient=user,
                    verb=_("تذكير الورد اليومي"),
                    description=_("حان وقت قراءة وردك اليومي من القرآن الكريم."),
                    timestamp=now,
                    target_content_type=ContentType.objects.get_for_model(PrayerReminder),
                    target_object_id=reminder_setting.pk,
                )
                reminder_setting.is_notified_werd_today = True
                reminder_setting.save(update_fields=['is_notified_werd_today'])
                print(f"Notification created for Daily Werd for user {user.username}")
        
        # إعادة تعيين حالة الإشعارات اليومية في بداية يوم جديد
        if reminder_setting.last_notification_reset_date != today_date:
            reminder_setting.is_notified_morning_adhkar_today = False
            reminder_setting.is_notified_evening_adhkar_today = False
            reminder_setting.is_notified_werd_today = False
            reminder_setting.last_notification_reset_date = today_date
            reminder_setting.save(update_fields=[
                'is_notified_morning_adhkar_today', 
                'is_notified_evening_adhkar_today', 
                'is_notified_werd_today', 
                'last_notification_reset_date'
            ])
            print(f"Daily reminders reset for {user.username} for date {today_date}")


# --- Views الجديدة للقرآن والأذكار والأدعية ---

class QuranView(LoginRequiredMixin, TemplateView):
    template_name = 'prayer_times/quran_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        surah_number = self.request.GET.get('surah', '1')
        reciter = self.request.GET.get('reciter', 'ar.alafasy')

        api_url = f"https://api.alquran.cloud/v1/surah/{surah_number}/{reciter}"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data and data['data']:
                context['surah_data'] = data['data']
                context['surah_number'] = surah_number
                context['reciter'] = reciter
            else:
                messages.error(self.request, _("تعذر جلب بيانات السورة. يرجى المحاولة لاحقاً."))
        except requests.exceptions.RequestException as e:
            messages.error(self.request, _(f"خطأ في الاتصال بـ API القرآن: {e}"))
        except Exception as e:
            messages.error(self.request, _(f"حدث خطأ غير متوقع: {e}"))

        # قائمة بجميع سور القرآن الكريم الـ 114
        context['surahs_list'] = [
            {'number': 1, 'name': _('الفاتحة')},
            {'number': 2, 'name': _('البقرة')},
            {'number': 3, 'name': _('آل عمران')},
            {'number': 4, 'name': _('النساء')},
            {'number': 5, 'name': _('المائدة')},
            {'number': 6, 'name': _('الأنعام')},
            {'number': 7, 'name': _('الأعراف')},
            {'number': 8, 'name': _('الأنفال')},
            {'number': 9, 'name': _('التوبة')},
            {'number': 10, 'name': _('يونس')},
            {'number': 11, 'name': _('هود')},
            {'number': 12, 'name': _('يوسف')},
            {'number': 13, 'name': _('الرعد')},
            {'number': 14, 'name': _('إبراهيم')},
            {'number': 15, 'name': _('الحجر')},
            {'number': 16, 'name': _('النحل')},
            {'number': 17, 'name': _('الإسراء')},
            {'number': 18, 'name': _('الكهف')},
            {'number': 19, 'name': _('مريم')},
            {'number': 20, 'name': _('طه')},
            {'number': 21, 'name': _('الأنبياء')},
            {'number': 22, 'name': _('الحج')},
            {'number': 23, 'name': _('المؤمنون')},
            {'number': 24, 'name': _('النور')},
            {'number': 25, 'name': _('الفرقان')},
            {'number': 26, 'name': _('الشعراء')},
            {'number': 27, 'name': _('النمل')},
            {'number': 28, 'name': _('القصص')},
            {'number': 29, 'name': _('العنكبوت')},
            {'number': 30, 'name': _('الروم')},
            {'number': 31, 'name': _('لقمان')},
            {'number': 32, 'name': _('السجدة')},
            {'number': 33, 'name': _('الأحزاب')},
            {'number': 34, 'name': _('سبأ')},
            {'number': 35, 'name': _('فاطر')},
            {'number': 36, 'name': _('يس')},
            {'number': 37, 'name': _('الصافات')},
            {'number': 38, 'name': _('ص')},
            {'number': 39, 'name': _('الزمر')},
            {'number': 40, 'name': _('غافر')},
            {'number': 41, 'name': _('فصلت')},
            {'number': 42, 'name': _('الشورى')},
            {'number': 43, 'name': _('الزخرف')},
            {'number': 44, 'name': _('الدخان')},
            {'number': 45, 'name': _('الجاثية')},
            {'number': 46, 'name': _('الأحقاف')},
            {'number': 47, 'name': _('محمد')},
            {'number': 48, 'name': _('الفتح')},
            {'number': 49, 'name': _('الحجرات')},
            {'number': 50, 'name': _('ق')},
            {'number': 51, 'name': _('الذاريات')},
            {'number': 52, 'name': _('الطور')},
            {'number': 53, 'name': _('النجم')},
            {'number': 54, 'name': _('القمر')},
            {'number': 55, 'name': _('الرحمن')},
            {'number': 56, 'name': _('الواقعة')},
            {'number': 57, 'name': _('الحديد')},
            {'number': 58, 'name': _('المجادلة')},
            {'number': 59, 'name': _('الحشر')},
            {'number': 60, 'name': _('الممتحنة')},
            {'number': 61, 'name': _('الصف')},
            {'number': 62, 'name': _('الجمعة')},
            {'number': 63, 'name': _('المنافقون')},
            {'number': 64, 'name': _('التغابن')},
            {'number': 65, 'name': _('الطلاق')},
            {'number': 66, 'name': _('التحريم')},
            {'number': 67, 'name': _('الملك')},
            {'number': 68, 'name': _('القلم')},
            {'number': 69, 'name': _('الحاقة')},
            {'number': 70, 'name': _('المعارج')},
            {'number': 71, 'name': _('نوح')},
            {'number': 72, 'name': _('الجن')},
            {'number': 73, 'name': _('المزمل')},
            {'number': 74, 'name': _('المدثر')},
            {'number': 75, 'name': _('القيامة')},
            {'number': 76, 'name': _('الإنسان')},
            {'number': 77, 'name': _('المرسلات')},
            {'number': 78, 'name': _('النبأ')},
            {'number': 79, 'name': _('النازعات')},
            {'number': 80, 'name': _('عبس')},
            {'number': 81, 'name': _('التكوير')},
            {'number': 82, 'name': _('الانفطار')},
            {'number': 83, 'name': _('المطففين')},
            {'number': 84, 'name': _('الانشقاق')},
            {'number': 85, 'name': _('البروج')},
            {'number': 86, 'name': _('الطارق')},
            {'number': 87, 'name': _('الأعلى')},
            {'number': 88, 'name': _('الغاشية')},
            {'number': 89, 'name': _('الفجر')},
            {'number': 90, 'name': _('البلد')},
            {'number': 91, 'name': _('الشمس')},
            {'number': 92, 'name': _('الليل')},
            {'number': 93, 'name': _('الضحى')},
            {'number': 94, 'name': _('الشرح')},
            {'number': 95, 'name': _('التين')},
            {'number': 96, 'name': _('العلق')},
            {'number': 97, 'name': _('القدر')},
            {'number': 98, 'name': _('البينة')},
            {'number': 99, 'name': _('الزلزلة')},
            {'number': 100, 'name': _('العاديات')},
            {'number': 101, 'name': _('القارعة')},
            {'number': 102, 'name': _('التكاثر')},
            {'number': 103, 'name': _('العصر')},
            {'number': 104, 'name': _('الهمزة')},
            {'number': 105, 'name': _('الفيل')},
            {'number': 106, 'name': _('قريش')},
            {'number': 107, 'name': _('الماعون')},
            {'number': 108, 'name': _('الكوثر')},
            {'number': 109, 'name': _('الكافرون')},
            {'number': 110, 'name': _('النصر')},
            {'number': 111, 'name': _('المسد')},
            {'number': 112, 'name': _('الإخلاص')},
            {'number': 113, 'name': _('الفلق')},
            {'number': 114, 'name': _('الناس')},
        ]
        context['reciters_list'] = [
            {'id': 'ar.alafasy', 'name': _('مشاري العفاسي')},
            {'id': 'ar.abdulbasit', 'name': _('عبد الباسط عبد الصمد')},
            {'id': 'ar.minshawi', 'name': _('محمد صديق المنشاوي')},
            {'id': 'ar.saoodshuraym', 'name': _('سعود الشريم')},
            {'id': 'ar.mahermuaiqly', 'name': _('ماهر المعيقلي')},
        ]
        return context

class AdhkarView(LoginRequiredMixin, TemplateView):
    template_name = 'prayer_times/adhkar_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # API الجديد للأذكار
        adhkar_api_base_url = "https://ahegazy.github.io/muslimsazkar/"
        
        # قائمة بالملفات JSON للأذكار التي نريد جلبها
        adhkar_files = {
            _("أذكار الصباح"): "azkar_sabah.json",
            _("أذكار المساء"): "azkar_masa.json",
            _("أذكار النوم"): "azkar_elnoom.json",
            _("أذكار الاستيقاظ"): "azkar_elestkadh.json",
            _("أذكار الصلاة"): "azkar_elsalah.json",
            _("أذكار الطعام"): "azkar_elta3am.json",
            _("أذكار متنوعة"): "azkar_motafareka.json",
        }
        
        all_adhkar_data = []
        for category_name, file_name in adhkar_files.items():
            api_url = f"{adhkar_api_base_url}{file_name}"
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status() # يرفع استثناء لأخطاء 4xx/5xx
                data = response.json()
                if isinstance(data, list):
                    # إضافة اسم الفئة لكل ذكر
                    for dhikr in data:
                        dhikr['category'] = category_name
                    all_adhkar_data.extend(data)
                else:
                    print(f"Warning: Unexpected data format for {file_name}. Expected a list.")
            except requests.exceptions.RequestException as e:
                messages.error(self.request, _(f"خطأ في الاتصال بـ API الأذكار ({category_name}): {e}"))
            except Exception as e:
                messages.error(self.request, _(f"حدث خطأ غير متوقع أثناء جلب {category_name}: {e}"))

        context['adhkar_data'] = all_adhkar_data
        return context

class DuasView(LoginRequiredMixin, TemplateView):
    template_name = 'prayer_times/duas_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # API الجديد للأدعية
        duas_api_base_url = "https://ahegazy.github.io/muslimsazkar/"
        
        # ملفات JSON للأدعية (قد تحتاج إلى تحديدها بدقة من الـ API)
        # هذا الـ API لا يفصل الأذكار عن الأدعية بشكل صريح في مسارات مختلفة
        # لذا، سنحاول جلب بعض الملفات التي قد تحتوي على أدعية عامة أو تصفية من "أذكار متنوعة"
        # أو البحث عن API آخر مخصص للأدعية فقط.
        # كمثال، سأجلب "أذكار متنوعة" وأفترض أنها تحتوي على بعض الأدعية.
        # إذا كان هناك ملف JSON محدد للأدعية في هذا الـ API، يرجى تحديثه.
        duas_files = {
    _("دعاء الركوب"): "azkar_rakoub.json",
    _("دعاء السفر"): "azkar_safar.json",
    _("دعاء دخول المنزل"): "azkar_dkhoul_almanzel.json",
    _("دعاء الخروج من المنزل"): "azkar_khrog_manzel.json",
    _("دعاء دخول المسجد"): "azkar_dkhoul_masjed.json",
    _("دعاء الخروج من المسجد"): "azkar_khrog_masjed.json",
    _("دعاء دخول الخلاء"): "azkar_dkhoul_elkhala.json",
    _("دعاء الخروج من الخلاء"): "azkar_khrog_elkhala.json",
    _("الرقية الشرعية"): "roqia.json",
    _("دعاء الاستخارة"): "istikara.json",
    _("دعاء الكرب"): "azkar_alkrb.json",
    _("أدعية من القرآن"): "azkar_elquraan.json",
    _("أدعية عامة"): "azkar_motafareka.json"
}


        all_duas_data = []
        for category_name, file_name in duas_files.items():
            api_url = f"{duas_api_base_url}{file_name}"
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    for dua in data:
                        dua['category'] = category_name
                    all_duas_data.extend(data)
                else:
                    print(f"Warning: Unexpected data format for {file_name}. Expected a list.")
            except requests.exceptions.RequestException as e:
                messages.error(self.request, _(f"خطأ في الاتصال بـ API الأدعية ({category_name}): {e}"))
            except Exception as e:
                messages.error(self.request, _(f"حدث خطأ غير متوقع أثناء جلب {category_name}: {e}"))

        context['duas_data'] = all_duas_data
        return context
