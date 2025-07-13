from django.urls import path
from .views import (
    ExamResourcesView,
    AdminDashboardView,
    ReportListView,
    ReportDetailView,
    UserActivityListView,
)

app_name = 'exam_prep'

urlpatterns = [
    # Existing Exam Resources View
    path('', ExamResourcesView.as_view(), name='exam_resources'),

    # New Admin and Moderation Views
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-dashboard/reports/', ReportListView.as_view(), name='report_list'),
    path('admin-dashboard/reports/<int:pk>/', ReportDetailView.as_view(), name='report_detail'),
    path('admin-dashboard/user-activities/', UserActivityListView.as_view(), name='user_activity_list'),
]
