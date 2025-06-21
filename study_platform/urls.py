# study_platform/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # روابط تطبيق core هي الرئيسية
    path('files/', include('files_manager.urls')),
    path('news/', include('news.urls')),
    path('tasks/', include('tasks.urls')),
    # ... روابط التطبيقات الأخرى
    path('accounts/', include('django.contrib.auth.urls')), # لإدارة تسجيل الدخول والخروج وتغيير كلمة المرور
    path('notes/', include('notes.urls', namespace='notes')),
    path('exam-prep/', include('exam_prep.urls', namespace='exam_prep')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # هذا ليس ضرورياً عادةً أثناء التطوير إذا استخدمت STATICFILES_DIRS