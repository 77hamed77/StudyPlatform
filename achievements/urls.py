from django.urls import path
from .views import AllBadgesListView # استيراد الـ ListView مباشرة

app_name = 'achievements' # تعريف اسم التطبيق للمسارات

urlpatterns = [
    # مسار لعرض جميع الشارات
    # .as_view() يستخدم مع الـ Class-Based Views مثل ListView
    path('all/', AllBadgesListView.as_view(), name='all_badges'),
    # يمكنك إضافة المزيد من المسارات هنا لاحقاً إذا كان لديك المزيد من الـ Views
]
