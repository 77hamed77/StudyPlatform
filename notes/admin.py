from django.contrib import admin
from .models import NoteCategory, QuickNote
from django.utils.translation import gettext_lazy as _ # <--- هذا هو السطر الذي يجب إضافته

@admin.register(NoteCategory)
class NoteCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'notes_count', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at',)

    @admin.display(description=_('عدد الملاحظات')) # هنا يتم استخدام الدالة _
    def notes_count(self, obj):
        return obj.notes.count() # استخدام related_name 'notes'

@admin.register(QuickNote)
class QuickNoteAdmin(admin.ModelAdmin):
    list_display = ('title_snippet', 'user', 'category_name', 'updated_at', 'created_at')
    list_filter = ('user', 'category', 'updated_at', 'created_at')
    search_fields = ('title', 'content', 'user__username', 'category__name')
    raw_id_fields = ('user', 'category')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'content', 'category')
        }),
        (_('معلومات إضافية'), { # هنا يتم استخدام الدالة _
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('عنوان الملاحظة'), ordering='title') # هنا يتم استخدام الدالة _
    def title_snippet(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title

    @admin.display(description=_('التصنيف'), ordering='category__name') # هنا يتم استخدام الدالة _
    def category_name(self, obj):
        return obj.category.name if obj.category else '-'