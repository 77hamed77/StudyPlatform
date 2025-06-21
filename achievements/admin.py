from django.contrib import admin
from .models import Badge, UserBadge
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html # لعرض الصور/الأيقونات

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_icon', 'badge_type_key', 'criteria_snippet', 'order', 'earned_count')
    search_fields = ('name', 'description', 'criteria_description', 'badge_type_key')
    list_editable = ('order',)
    fields = ('name', 'description', 'badge_type_key', 'criteria_description', 'icon_class', 'icon_image', 'order')

    @admin.display(description=_('الأيقونة'))
    def display_icon(self, obj):
        if obj.icon_image:
            return format_html('<img src="{}" style="max-height: 30px; max-width: 30px;" />', obj.icon_image.url)
        elif obj.icon_class:
            return format_html('<i class="{}" style="font-size: 1.5rem;"></i>', obj.icon_class)
        return "-"

    @admin.display(description=_('معيار التحقيق'))
    def criteria_snippet(self, obj):
        if obj.criteria_description:
            return obj.criteria_description[:70] + "..." if len(obj.criteria_description) > 70 else obj.criteria_description
        return "-"
    
    @admin.display(description=_('عدد مرات الاكتساب'))
    def earned_count(self, obj):
        return obj.earned_by_users.count() # استخدام related_name

    # يمكنك إضافة إجراء لإنشاء الشارات الافتراضية إذا لم تكن موجودة
    # def sync_default_badges(self, request, queryset):
    #     # ... منطق لمقارنة BADGE_KEYS مع الموجود في قاعدة البيانات وإنشاء الناقص ...
    #     pass
    # actions = [sync_default_badges]

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'badge_name', 'earned_at_display')
    list_filter = ('badge', 'earned_at', ('user', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__username', 'badge__name')
    autocomplete_fields = ['user', 'badge'] # جيد هنا
    readonly_fields = ('earned_at',) # تاريخ الاكتساب لا يجب تعديله

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description=_('الشارة'), ordering='badge__name')
    def badge_name(self, obj):
        return obj.badge.name

    @admin.display(description=_('تاريخ الاكتساب'), ordering='earned_at')
    def earned_at_display(self, obj):
        return obj.earned_at.strftime("%Y-%m-%d %H:%M")