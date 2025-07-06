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
                            # تأكد من أن prayer_type موجود في PRAYER_CHOICES
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

        # التحقق من التذكيرات وإنشاء الإشعارات (فقط لليوم الحالي)
        if target_date == timezone.now().date():
            self._check_and_create_reminders(request.user, prayer_times_qs, reminder_setting)

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
        if 'notification_time_before' in request.POST or 'enable_notifications' in request.POST or \
           'daily_werd_reminder_enabled' in request.POST or 'daily_werd_reminder_time' in request.POST:
            
            reminder_setting, created = PrayerReminder.objects.get_or_create(user=request.user)
            
            try:
                minutes_before = int(request.POST.get('notification_time_before', reminder_setting.notification_time_before))
                reminder_setting.notification_time_before = max(0, min(60, minutes_before))
            except ValueError:
                messages.error(request, _("قيمة غير صالحة لدقائق التذكير."))

            reminder_setting.enabled = request.POST.get('enable_notifications') == 'on'
            
            # --- حفظ إعدادات الورد اليومي ---
            reminder_setting.daily_werd_reminder_enabled = request.POST.get('daily_werd_reminder_enabled') == 'on'
            werd_time_str = request.POST.get('daily_werd_reminder_time')
            if werd_time_str:
                try:
                    werd_time_obj = datetime.strptime(werd_time_str, '%H:%M').time()
                    reminder_setting.daily_werd_reminder_time = werd_time_obj
                except ValueError:
                    messages.error(request, _("تنسيق وقت الورد اليومي غير صالح. استخدم HH:MM."))
            # ----------------------------------

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
        """
        يتحقق من أوقات الصلاة وينشئ إشعارات للمستخدم إذا حان وقت التذكير،
        بالإضافة إلى أذكار الصباح والمساء والورد اليومي.
        """
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

                # تحقق إذا كان وقت التذكير قد حان للتو ولم يتم إرسال الإشعار بعد
                # ويكون وقت الصلاة في المستقبل (لتجنب إشعارات الصلوات الماضية)
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
        # نستخدم PrayerTime.objects.filter().first() للحصول على وقت الصلاة لليوم
        fajr_time_obj = PrayerTime.objects.filter(user=user, date=today_date, prayer_type='fajr').first()
        asr_time_obj = PrayerTime.objects.filter(user=user, date=today_date, prayer_type='asr').first()

        # تذكير أذكار الصباح (بعد الفجر بـ 15 دقيقة، أو وقت محدد)
        if fajr_time_obj:
            morning_adhkar_reminder_time = timezone.make_aware(
                datetime.combine(today_date, fajr_time_obj.time),
                timezone.get_current_timezone()
            ) + timedelta(minutes=15) # 15 دقيقة بعد الفجر

            # استخدم حقل is_notified_morning_adhkar في PrayerReminder لتتبع الإشعار
            if morning_adhkar_reminder_time <= now < (morning_adhkar_reminder_time + timedelta(minutes=1)) and not reminder_setting.is_notified_morning_adhkar_today:
                Notification.objects.create(
                    recipient=user,
                    verb=_("تذكير أذكار الصباح"),
                    description=_("حان وقت قراءة أذكار الصباح."),
                    timestamp=now,
                    # يمكنك ربطها بصفحة الأذكار
                    target_content_type=ContentType.objects.get_for_model(PrayerReminder),
                    target_object_id=reminder_setting.pk,
                )
                reminder_setting.is_notified_morning_adhkar_today = True # تحديث الحقل
                reminder_setting.save(update_fields=['is_notified_morning_adhkar_today'])
                print(f"Notification created for Morning Adhkar for user {user.username}")

        # تذكير أذكار المساء (بعد العصر بـ 15 دقيقة، أو وقت محدد)
        if asr_time_obj:
            evening_adhkar_reminder_time = timezone.make_aware(
                datetime.combine(today_date, asr_time_obj.time),
                timezone.get_current_timezone()
            ) + timedelta(minutes=15) # 15 دقيقة بعد العصر

            # استخدم حقل is_notified_evening_adhkar في PrayerReminder لتتبع الإشعار
            if evening_adhkar_reminder_time <= now < (evening_adhkar_reminder_time + timedelta(minutes=1)) and not reminder_setting.is_notified_evening_adhkar_today:
                Notification.objects.create(
                    recipient=user,
                    verb=_("تذكير أذكار المساء"),
                    description=_("حان وقت قراءة أذكار المساء."),
                    timestamp=now,
                    target_content_type=ContentType.objects.get_for_model(PrayerReminder),
                    target_object_id=reminder_setting.pk,
                )
                reminder_setting.is_notified_evening_adhkar_today = True # تحديث الحقل
                reminder_setting.save(update_fields=['is_notified_evening_adhkar_today'])
                print(f"Notification created for Evening Adhkar for user {user.username}")

        # تذكير الورد اليومي (في وقت محدد يختاره المستخدم)
        if reminder_setting.daily_werd_reminder_enabled and reminder_setting.daily_werd_reminder_time:
            werd_reminder_datetime = timezone.make_aware(
                datetime.combine(today_date, reminder_setting.daily_werd_reminder_time),
                timezone.get_current_timezone()
            )

            # استخدم حقل is_notified_werd_today في PrayerReminder لتتبع الإشعار
            if werd_reminder_datetime <= now < (werd_reminder_datetime + timedelta(minutes=1)) and not reminder_setting.is_notified_werd_today:
                Notification.objects.create(
                    recipient=user,
                    verb=_("تذكير الورد اليومي"),
                    description=_("حان وقت قراءة وردك اليومي من القرآن الكريم."),
                    timestamp=now,
                    target_content_type=ContentType.objects.get_for_model(PrayerReminder),
                    target_object_id=reminder_setting.pk,
                )
                reminder_setting.is_notified_werd_today = True # تحديث الحقل
                reminder_setting.save(update_fields=['is_notified_werd_today'])
                print(f"Notification created for Daily Werd for user {user.username}")
        
        # إعادة تعيين حالة الإشعارات اليومية في بداية يوم جديد
        # هذا يتطلب تشغيل Celery Beat أو مهمة مجدولة
        # For now, we'll just reset them if the date changes
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
    template_name = 'prayer_times/quran_page.html' # سيتم إنشاء هذا القالب

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        surah_number = self.request.GET.get('surah', '1') # افتراضياً سورة الفاتحة
        reciter = self.request.GET.get('reciter', 'ar.alafasy') # افتراضياً العفاسي

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

        # قائمة بأسماء السور للـ dropdown (يمكن جلبها من API أو تخزينها محلياً)
        # لتبسيط الأمر، سأضع قائمة بسيطة بأول 10 سور
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
            # ... يمكنك إضافة جميع السور الـ 114 هنا
        ]
        # قائمة بالقراء (Reciters) المدعومين من API
        context['reciters_list'] = [
            {'id': 'ar.alafasy', 'name': _('مشاري العفاسي')},
            {'id': 'ar.abdulbasit', 'name': _('عبد الباسط عبد الصمد')},
            {'id': 'ar.minshawi', 'name': _('محمد صديق المنشاوي')},
            {'id': 'ar.saoodshuraym', 'name': _('سعود الشريم')},
            {'id': 'ar.mahermuaiqly', 'name': _('ماهر المعيقلي')},
            # ... والمزيد
        ]
        return context

class AdhkarView(LoginRequiredMixin, TemplateView):
    template_name = 'prayer_times/adhkar_page.html' # سيتم إنشاء هذا القالب

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_url = "https://hisnulmuslim-api.vercel.app/api/ar" # API يوفر جميع الأذكار والأدعية

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # API هذا يعيد قائمة كبيرة، سنحتاج لتصفيتها للأذكار فقط
            # بناءً على بنية الـ API، قد تحتاج إلى تحديد الفئات التي تمثل الأذكار
            # كمثال، سأفترض أن الأذكار هي التي تحتوي على "أذكار" في عنوانها
            adhkar_categories = [
                "أذكار الصباح والمساء",
                "أذكار النوم",
                "أذكار الاستيقاظ",
                "أذكار الصلاة"
            ]
            
            # تصفية الأذكار
            filtered_adhkar = []
            if data and isinstance(data, list):
                for item in data:
                    if item.get('category') in adhkar_categories: # يمكنك تحسين هذا الشرط
                        filtered_adhkar.append(item)
            
            # إذا لم يتم العثور على أذكار محددة، قد تحتاج إلى جلبها كلها
            if not filtered_adhkar and data and isinstance(data, list):
                # إذا لم تنجح الفلترة، اعرض كل شيء أو جزء منه
                filtered_adhkar = data # لعرض كل شيء كاحتياط
                messages.warning(self.request, _("لم يتم العثور على أذكار محددة. يتم عرض جميع الأدعية والأذكار المتاحة."))

            context['adhkar_data'] = filtered_adhkar
        except requests.exceptions.RequestException as e:
            messages.error(self.request, _(f"خطأ في الاتصال بـ API الأذكار: {e}"))
        except Exception as e:
            messages.error(self.request, _(f"حدث خطأ غير متوقع: {e}"))
        return context

class DuasView(LoginRequiredMixin, TemplateView):
    template_name = 'prayer_times/duas_page.html' # سيتم إنشاء هذا القالب

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_url = "https://hisnulmuslim-api.vercel.app/api/ar" # نفس API الأذكار

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # تصفية الأدعية (يمكنك تحسين منطق التصفية بناءً على الفئات المتاحة في API)
            duas_categories = [
                "دعاء الاستفتاح",
                "دعاء لبس الثوب",
                "دعاء دخول الخلاء",
                "دعاء الخروج من الخلاء",
                "دعاء قبل النوم",
                "دعاء الهم والحزن",
                "دعاء قنوت الوتر",
                "دعاء السفر",
                "دعاء الاستخارة",
            ]
            
            filtered_duas = []
            if data and isinstance(data, list):
                for item in data:
                    if item.get('category') in duas_categories: # يمكنك تحسين هذا الشرط
                        filtered_duas.append(item)
            
            # إذا لم يتم العثور على أدعية محددة، قد تحتاج إلى جلبها كلها
            if not filtered_duas and data and isinstance(data, list):
                filtered_duas = data # لعرض كل شيء كاحتياط

            context['duas_data'] = filtered_duas
        except requests.exceptions.RequestException as e:
            messages.error(self.request, _(f"خطأ في الاتصال بـ API الأدعية: {e}"))
        except Exception as e:
            messages.error(self.request, _(f"حدث خطأ غير متوقع: {e}"))
        return context

