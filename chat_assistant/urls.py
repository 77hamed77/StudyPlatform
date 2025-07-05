from django.urls import path
from .views import ChatAssistantView

app_name = 'chat_assistant'

urlpatterns = [
    path('', ChatAssistantView.as_view(), name='chat_assistant'),
]