from django.urls import path
from .views import PrayerTimesView # لا نحتاج get_prayer_times_json هنا

app_name = 'prayer_times'

urlpatterns = [
    path('', PrayerTimesView.as_view(), name='prayer_times_list'),
    # لا حاجة لـ 'api/' نقطة نهاية منفصلة إذا كان الـ JS يعتمد على البيانات المضمنة في القالب
    # أو يمكن إضافتها إذا كنت تخطط لجلب البيانات بشكل ديناميكي بالكامل عبر AJAX
]
