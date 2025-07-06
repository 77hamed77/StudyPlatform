from django.urls import path
from .views import PrayerTimesView, QuranView, AdhkarView, DuasView, HadithView # استيراد HadithView

app_name = 'prayer_times'

urlpatterns = [
    path('', PrayerTimesView.as_view(), name='prayer_times_list'),
    path('quran/', QuranView.as_view(), name='quran_page'),
    path('adhkar/', AdhkarView.as_view(), name='adhkar_page'),
    path('duas/', DuasView.as_view(), name='duas_page'),
    path('hadith/', HadithView.as_view(), name='hadith_page'), # <--- مسار جديد للأحاديث
]
