from django.contrib import admin
from .models import Task
from django.utils.translation import gettext_lazy as _ # <--- هذا هو السطر الذي يجب إضافته

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'subject_name', # دالة مخصصة لعرض اسم المادة
        'status',
        'due_date',
        'is_overdue_display', # دالة مخصصة لعرض إذا كانت متأخرة
        'created_at'
    )
    list_filter = ('status', 'due_date', 'user', 'subject')
    search_fields = ('title', 'description', 'user__username', 'subject__name')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'description')
        }),
        (_('التصنيف والمواعيد'), { # هنا يتم استخدام الدالة _
            'fields': ('subject', 'due_date', 'status')
        }),
        (_('معلومات إضافية'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ['user', 'subject']

    @admin.display(description=_('المادة'), ordering='subject__name')
    def subject_name(self, obj):
        return obj.subject.name if obj.subject else '-'

    @admin.display(description=_('متأخرة؟'), boolean=True, ordering='due_date')
    def is_overdue_display(self, obj):
        return obj.is_overdue