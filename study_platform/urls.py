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
    path('chat/', include('chat_assistant.urls')),  # روابط تطبيق المساعد الذكي للدردشة
    path('prayer/', include('prayer_times.urls')),  # روابط تطبيق أوقات الصلاة
    path('achievements/', include('achievements.urls')),  # روابط تطبيق الإنجازات
    path('accounts/', include('django.contrib.auth.urls')),  # تسجيل الدخول/الخروج وتغيير كلمة المرور
    path('notes/', include('notes.urls', namespace='notes')),
    path('exam-prep/', include('exam_prep.urls', namespace='exam_prep')),
]

# هذا الجزء مخصص لخدمة الملفات الثابتة (STATIC) وملفات الوسائط (MEDIA)
# في وضع التطوير (DEBUG=True) فقط.
# في وضع الإنتاج، يتم التعامل مع STATIC بواسطة Whitenoise و MEDIA بواسطة Supabase Storage.
if settings.DEBUG:
    # لخدمة الملفات الثابتة محلياً
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # لخدمة ملفات الوسائط (المرفوعة من المستخدمين) محلياً
    # هذا الشرط مهم: لا تخدم MEDIA محلياً إذا كنت تستخدم تخزيناً سحابياً (مثل Supabase)
    # إلا إذا كان لديك منطق احتياطي للتخزين المحلي في settings.py
    # بما أنك تستخدم Supabase Storage، فإن MEDIA_URL في settings.py سيشير إلى Supabase.
    # لذلك، هذا السطر قد لا يكون ضرورياً أو قد يتعارض في بعض الحالات.
    # ومع ذلك، إذا كان لديك fallback للتخزين المحلي في settings.py، فقد تحتاج إليه.
    # سأبقيه هنا مع ملاحظة، ولكن في الإنتاج لن يكون له تأثير.
    if hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT') and \
       settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage':
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

