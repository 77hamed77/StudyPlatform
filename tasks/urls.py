# tasks/urls.py
from django.urls import path
from . import views

app_name = 'tasks'  # <--- هذا هو السطر المهم جداً الذي يحدد اسم التطبيق

urlpatterns = [
    # قائمة المهام (الرئيسية للتطبيق)
    path('', views.TaskListView.as_view(), name='task_list'),

    # إنشاء مهمة جديدة
    path('new/', views.TaskCreateView.as_view(), name='task_create'),

    # تفاصيل مهمة معينة (تستخدم Primary Key 'pk' للمهمة)
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),

    # تعديل مهمة معينة
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),

    # حذف مهمة معينة
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),

    # مسارات لتغيير حالة المهمة (تستخدم POST requests)
    path('<int:pk>/mark-complete/', views.mark_task_complete, name='task_mark_complete'),
    path('<int:pk>/mark-inprogress/', views.mark_task_inprogress, name='task_mark_inprogress'),

    # *** قم بإزالة أي سطر يشبه path('tasks/', include('tasks.urls', ...)) من هنا ***
]