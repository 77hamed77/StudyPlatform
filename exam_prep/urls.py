from django.urls import path
from . import views

app_name = 'exam_prep'

urlpatterns = [
    path('', views.ExamResourcesView.as_view(), name='exam_resources'),
]