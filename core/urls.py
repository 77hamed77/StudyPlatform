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
    
    # مسارات الموارد التعليمية مع دعم التقييمات والمفضلة
    path('educational-resources/', views.EducationalResourcesView.as_view(), name='educational_resources'),
    path('educational-resources/rate/', views.EducationalResourcesView.as_view(), name='rate_resource'), # POST endpoint for rating
    path('educational-resources/toggle-favorite/', views.toggle_favorite_resource, name='toggle_favorite_resource'),
    path('educational-resources/favorites/', views.UserFavoriteResourcesListView.as_view(), name='favorite_resources_list'),


    # --- مسارات الأدوات والمرافق (من التحديث السابق) ---
    path('tools/calculator/', views.ScientificCalculatorView.as_view(), name='scientific_calculator'),
    path('tools/unit-converter/', views.UnitConverterView.as_view(), name='unit_converter'),
    path('tools/faq/', views.FAQListView.as_view(), name='faq_list'),
    path('tools/discussion-board/', views.DiscussionBoardListView.as_view(), name='discussion_board'),
    path('tools/discussion-board/<int:pk>/', views.DiscussionPostDetailView.as_view(), name='discussion_post_detail'),
    path('tools/academic-progress/', views.AcademicProgressView.as_view(), name='academic_progress'),
]
