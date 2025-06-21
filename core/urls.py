from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications_list'),
    # يمكنك إضافة مسارات AJAX لتمييز الإشعارات كمقروءة هنا إذا أردت
    # path('ajax/notifications/mark-as-read/<int:notification_id>/', views.mark_notification_as_read_ajax, name='ajax_mark_notification_read'),
    # path('ajax/notifications/mark-all-as-read/', views.mark_all_notifications_as_read_ajax, name='ajax_mark_all_notifications_read'),
]