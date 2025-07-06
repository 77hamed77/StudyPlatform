from django.urls import path
from .views import PrayerTimesView, QuranView, AdhkarView, DuasView

app_name = 'prayer_times'

urlpatterns = [
    path('', PrayerTimesView.as_view(), name='prayer_times_list'),
    path('quran/', QuranView.as_view(), name='quran_page'),
    path('adhkar/', AdhkarView.as_view(), name='adhkar_page'),
    path('duas/', DuasView.as_view(), name='duas_page'),
]
# Note: Ensure that the views (PrayerTimesView, QuranView, AdhkarView, DuasView) are defined in views.py