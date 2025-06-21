from django.contrib import admin
from .models import NewsCategory, NewsItem
from django.utils.translation import gettext_lazy as _

@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'news_items_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)} # إنشاء slug تلقائيًا من الاسم أثناء الكتابة

    @admin.display(description=_('عدد الأخبار'))
    def news_items_count(self, obj):
        return obj.news_items.count() # استخدام related_name 'news_items'

@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'author_username', # دالة مخصصة
        'publication_date',
        'is_published',
        'is_important',
    )
    list_filter = ('is_published', 'is_important', 'publication_date', 'category', 'author')
    search_fields = ('title', 'content', 'excerpt', 'author__username', 'category__name')
    list_editable = ('is_published', 'is_important') # السماح بتعديل هذه الحقول مباشرة
    prepopulated_fields = {'slug': ('title',)} # إنشاء slug تلقائيًا من العنوان
    date_hierarchy = 'publication_date' # إضافة تصفح هرمي حسب التاريخ
    readonly_fields = ('author',) # جعل المؤلف للقراءة فقط إذا تم تعيينه تلقائيًا
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'excerpt')
        }),
        (_('التصنيف والصورة'), {
            'fields': ('category', 'image')
        }),
        (_('النشر والإعدادات'), {
            'fields': ('publication_date', 'is_published', 'is_important')
            # 'author' سيتم تعيينه تلقائيًا في save_model
        }),
    )
    autocomplete_fields = ['category', 'author'] # إذا كان لديك عدد كبير من التصنيفات أو المؤلفين

    @admin.display(description=_('الناشر'), ordering='author__username')
    def author_username(self, obj):
        return obj.author.username if obj.author else '-'

    def save_model(self, request, obj, form, change):
        """
        تعيين المستخدم الحالي كمؤلف للخبر عند إنشائه من لوحة التحكم
        إذا لم يكن هناك مؤلف محدد بالفعل.
        """
        if not obj.author_id: # author_id لتجنب جلب كائن User إذا لم يكن ضروريًا
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        # تحسين أداء جلب البيانات ذات الصلة
        return super().get_queryset(request).select_related('category', 'author')