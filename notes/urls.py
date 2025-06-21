from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.QuickNoteListView.as_view(), name='note_list'),
    path('new/', views.QuickNoteCreateView.as_view(), name='note_create'),
    path('<int:pk>/', views.QuickNoteDetailView.as_view(), name='note_detail'),
    path('<int:pk>/edit/', views.QuickNoteUpdateView.as_view(), name='note_edit'),
    path('<int:pk>/delete/', views.QuickNoteDeleteView.as_view(), name='note_delete'),

    path('categories/new/', views.NoteCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.NoteCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.NoteCategoryDeleteView.as_view(), name='category_delete'),
    # يمكنك إضافة مسار لعرض قائمة التصنيفات إذا أردت:
    # path('categories/', views.NoteCategoryListView.as_view(), name='category_list'),
]