from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # روابط تطبيق core هي الرئيسية
    path('files/', include('files_manager.urls')),
    path('news/', include('news.urls')),
    path('tasks/', include('tasks.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # تسجيل الدخول/الخروج وتغيير كلمة المرور
    path('notes/', include('notes.urls', namespace='notes')),
    path('exam-prep/', include('exam_prep.urls', namespace='exam_prep')),
]

# لا تضف أبداً media/static أثناء التطوير لتقديم ملفات media من السيرفر المحلي
# لأنك تعتمد على التخزين السحابي فقط (S3/Supabase)
# إذا كنت تريد تقديم ملفات static فقط أثناء التطوير (وليس media) يمكنك إبقاء السطر التالي
if settings.DEBUG:
    if hasattr(settings, 'STATIC_URL') and hasattr(settings, 'STATIC_ROOT'):
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        
urlpatterns = [
    path('files/', include('files_manager.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)