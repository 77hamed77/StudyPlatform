from django.urls import path
from . import views

app_name = 'files_manager'

urlpatterns = [
    path('main/', views.MainFileListView.as_view(), name='main_file_list'),
    path('main/<int:pk>/', views.MainFileDetailView.as_view(), name='main_file_detail'),
    
    path('summaries/', views.StudentSummaryListView.as_view(), name='student_summary_list'),
    path('summaries/my-uploads/', views.MyStudentSummariesListView.as_view(), name='my_summaries_list'),
    path('summaries/upload/', views.StudentSummaryUploadView.as_view(), name='student_summary_upload'),

    path('ajax/toggle-read-status/', views.toggle_file_read_status, name='toggle_file_read_status'), # تم تغيير المسار ليكون أوضح أنه AJAX
]