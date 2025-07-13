from django.contrib import admin
from .models import ExamPrayer, ExamTip, Report, UserActivity # استيراد النماذج الجديدة
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType # لاستخدام ContentType في الإدارة
from django.urls import reverse # لاستخدام reverse في الروابط
from django.utils.html import format_html # لعرض HTML مخصص في الإدارة


@admin.register(ExamPrayer)
class ExamPrayerAdmin(admin.ModelAdmin):
    list_display = ('title_display', 'text_snippet', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'text')
    list_editable = ('order', 'is_active')
    fields = ('title', 'text', 'order', 'is_active')

    @admin.display(description=_('العنوان'), ordering='title')
    def title_display(self, obj):
        return obj.title if obj.title else _("(دعاء بدون عنوان)")

    @admin.display(description=_('مقتطف من الدعاء'))
    def text_snippet(self, obj):
        return obj.text[:70] + "..." if len(obj.text) > 70 else obj.text


@admin.register(ExamTip)
class ExamTipAdmin(admin.ModelAdmin):
    list_display = ('title', 'category_display', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')
    fields = ('title', 'description', 'category', 'order', 'is_active')

    @admin.display(description=_('التصنيف'), ordering='category')
    def category_display(self, obj):
        return obj.get_category_display()


# --- New Admin Classes for Report and UserActivity ---

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter_display', 'reported_object_link', 'reason_snippet', 'status', 'reported_at', 'reviewed_by_display')
    list_filter = ('status', 'reported_at', 'content_type', 'reporter')
    search_fields = ('reporter__username', 'reason', 'admin_notes')
    date_hierarchy = 'reported_at' # يضيف شريط تصفية حسب التاريخ
    readonly_fields = ('reporter', 'content_type', 'object_id', 'reported_at', 'content_object') # لا يمكن تعديل هذه الحقول بعد الإنشاء
    fieldsets = (
        (None, {
            'fields': ('reporter', 'content_object', 'reason', 'reported_at')
        }),
        (_('حالة المراجعة'), {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes')
        }),
    )

    # يعرض اسم المُبلغ
    @admin.display(description=_('المُبلغ'), ordering='reporter__username')
    def reporter_display(self, obj):
        return obj.reporter.username if obj.reporter else _("مجهول")

    # يعرض رابطًا للكائن المبلغ عنه في لوحة الإدارة
    @admin.display(description=_('الكائن المبلغ عنه'))
    def reported_object_link(self, obj):
        if obj.content_object:
            # بناء رابط لكائن الإدارة، بافتراض أن لديه admin URL
            try:
                # مثال: /admin/app_label/model_name/object_id/change/
                admin_url = reverse(
                    f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                    args=[obj.object_id]
                )
                return format_html('<a href="{}">{} (ID: {})</a>', admin_url, str(obj.content_object), obj.object_id)
            except Exception:
                return str(obj.content_object) + f" (ID: {obj.object_id})"
        return "-"

    # يعرض مقتطفًا من سبب الإبلاغ
    @admin.display(description=_('سبب الإبلاغ'))
    def reason_snippet(self, obj):
        return obj.reason[:70] + "..." if len(obj.reason) > 70 else obj.reason

    # يعرض اسم المشرف الذي راجع الإبلاغ
    @admin.display(description=_('تمت المراجعة بواسطة'), ordering='reviewed_by__username')
    def reviewed_by_display(self, obj):
        return obj.reviewed_by.username if obj.reviewed_by else "-"

    # عند حفظ الإبلاغ في لوحة الإدارة، قم بتحديث حقول المراجعة
    def save_model(self, request, obj, form, change):
        if obj.status != 'pending' and not obj.reviewed_by:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'activity_type', 'timestamp', 'related_object', 'details_snippet')
    list_filter = ('activity_type', 'timestamp', ('user', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__username', 'activity_type', 'details')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'activity_type', 'timestamp', 'content_type', 'object_id', 'details', 'content_object') # جميع الحقول للقراءة فقط

    # يعرض اسم المستخدم
    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_display(self, obj):
        return obj.user.username

    # يعرض رابطًا للكائن المرتبط بالنشاط
    @admin.display(description=_('الكائن المرتبط'))
    def related_object(self, obj):
        if obj.content_object:
            try:
                admin_url = reverse(
                    f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                    args=[obj.object_id]
                )
                return format_html('<a href="{}">{} (ID: {})</a>', admin_url, str(obj.content_object), obj.object_id)
            except Exception:
                return str(obj.content_object) + f" (ID: {obj.object_id})"
        return "-"

    # يعرض مقتطفًا من تفاصيل JSON
    @admin.display(description=_('تفاصيل'))
    def details_snippet(self, obj):
        if obj.details:
            import json
            details_str = json.dumps(obj.details, ensure_ascii=False)
            return details_str[:70] + "..." if len(details_str) > 70 else details_str
        return "-"

