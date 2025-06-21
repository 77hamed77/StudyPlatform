from django.contrib import admin
from .models import ExamPrayer, ExamTip
from django.utils.translation import gettext_lazy as _

@admin.register(ExamPrayer)
class ExamPrayerAdmin(admin.ModelAdmin):
    list_display = ('title_display', 'text_snippet', 'order', 'is_active')
    list_filter = ('is_active',) # إضافة فلتر حسب الحالة
    search_fields = ('title', 'text')
    list_editable = ('order', 'is_active') # السماح بتعديل الترتيب والحالة مباشرة
    fields = ('title', 'text', 'order', 'is_active') # تحديد ترتيب الحقول في صفحة التعديل

    @admin.display(description=_('العنوان'), ordering='title')
    def title_display(self, obj):
        return obj.title if obj.title else _("(دعاء بدون عنوان)")

    @admin.display(description=_('مقتطف من الدعاء'))
    def text_snippet(self, obj):
        return obj.text[:70] + "..." if len(obj.text) > 70 else obj.text

@admin.register(ExamTip)
class ExamTipAdmin(admin.ModelAdmin):
    list_display = ('title', 'category_display', 'order', 'is_active') # استخدام category_display
    list_filter = ('category', 'is_active') # إضافة فلتر حسب الحالة
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')
    fields = ('title', 'description', 'category', 'order', 'is_active') # تحديد ترتيب الحقول

    @admin.display(description=_('التصنيف'), ordering='category')
    def category_display(self, obj):
        return obj.get_category_display() # لعرض التسمية المترجمة للتصنيف