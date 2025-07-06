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
    path('notifications/mark_all_read/', views.mark_all_notifications_read, name='notification_mark_all_read'),
    path('notifications/mark_read/', views.mark_notification_read, name='notification_mark_read'),
]