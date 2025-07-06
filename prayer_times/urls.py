from django.urls import path
from .views import PrayerTimesView

app_name = 'prayer_times'

urlpatterns = [
    path('', PrayerTimesView.as_view(), name='prayer_times'),
]