"""
URL configuration for tasks app.
"""
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Task CRUD operations
    path('tasks/', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    
    # Task analysis and suggestions
    path('tasks/analyze/', views.TaskAnalyzeView.as_view(), name='analyze'),
    path('tasks/suggest/', views.TaskSuggestView.as_view(), name='suggest'),
]

