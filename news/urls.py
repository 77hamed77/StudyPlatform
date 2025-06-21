# news/urls.py
from django.urls import path, re_path # استيراد re_path
from . import views
from django.utils.translation import gettext_lazy as _ # ليس ضروريًا هنا ولكن جيد إبقاؤه

app_name = 'news'

urlpatterns = [
    path('', views.NewsListView.as_view(), name='news_list'),

    path('category/<slug:category_slug>/', views.NewsListView.as_view(), name='news_list_by_category'),
    
    # تم تعديل هذا المسار ليستخدم re_path ويقبل الحروف العربية في الـ slug
    re_path(
        r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<slug>[-\w\u0600-\u06FF]+)/$',
        views.NewsDetailView.as_view(),
        name='news_detail'
    ),

    path('new/', views.NewsCreateView.as_view(), name='news_create'),

    # تم تعديل هذه المسارات أيضًا لتستخدم re_path وتدعم الـ slug العربي
    re_path(
        r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<slug>[-\w\u0600-\u06FF]+)/edit/$',
        views.NewsUpdateView.as_view(),
        name='news_edit'
    ),
    re_path(
        r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<slug>[-\w\u0600-\u06FF]+)/delete/$',
        views.NewsDeleteView.as_view(),
        name='news_delete'
    ),
]