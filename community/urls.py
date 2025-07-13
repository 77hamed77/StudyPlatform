from django.urls import path
from . import views

app_name = 'community' # Define app_name for namespacing URLs

urlpatterns = [
    # Study Group URLs
    path('study-groups/', views.StudyGroupListView.as_view(), name='study_group_list'),
    path('study-groups/create/', views.StudyGroupCreateView.as_view(), name='study_group_create'),
    path('study-groups/<int:pk>/', views.StudyGroupDetailView.as_view(), name='study_group_detail'),
    
    # AJAX Endpoints for Study Groups
    path('study-groups/<int:pk>/join-leave/', views.join_leave_group, name='join_leave_group'),
    path('study-groups/<int:pk>/send-message/', views.send_group_message, name='send_group_message'),
    path('study-groups/<int:pk>/get-messages/', views.get_group_messages, name='get_group_messages'),

    # Future: Private Messaging URLs (placeholders)
    # path('messages/', views.PrivateMessageListView.as_view(), name='private_message_list'),
    # path('messages/send/<int:user_id>/', views.PrivateMessageSendView.as_view(), name='private_message_send'),

    # Future: Q&A Platform URLs (placeholders)
    # path('qa/', views.QuestionListView.as_view(), name='question_list'),
    # path('qa/ask/', views.QuestionCreateView.as_view(), name='question_create'),
    # path('qa/<int:pk>/', views.QuestionDetailView.as_view(), name='question_detail'),
    # path('qa/answer/<int:question_pk>/', views.AnswerCreateView.as_view(), name='answer_create'),
    # path('qa/vote/<int:content_type_id>/<int:object_id>/', views.vote_view, name='vote'),
]
