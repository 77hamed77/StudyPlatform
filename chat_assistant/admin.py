from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ChatInteraction # استيراد النموذج من models.py

@admin.register(ChatInteraction)
class ChatInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'main_file_title', 'question_preview', 'created_at')
    list_filter = ('user', 'main_file', 'created_at')
    search_fields = ('user__username', 'question', 'answer', 'main_file__title')
    readonly_fields = ('user', 'main_file', 'question', 'answer', 'created_at') # جعل كل الحقول للقراءة فقط

    @admin.display(description=_('عنوان المحاضرة'), ordering='main_file__title')
    def main_file_title(self, obj):
        """يعرض عنوان المحاضرة المرتبطة أو '-' إذا لم تكن هناك محاضرة."""
        return obj.main_file.title if obj.main_file else '-'

    @admin.display(description=_('معاينة السؤال'))
    def question_preview(self, obj):
        """يعرض جزءاً من السؤال لمعاينة أسهل."""
        return obj.question[:75] + '...' if len(obj.question) > 75 else obj.question

