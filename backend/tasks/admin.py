from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'due_date', 'due_time', 'importance', 'estimated_hours', 'role', 'is_overdue']
    list_filter = ['role', 'due_date', 'importance']
    search_fields = ['title']
    readonly_fields = ['created_at', 'is_overdue']

