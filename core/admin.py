from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Notification, DailyQuote, EducationalResource # تأكد من استيراد كل الموديلات التي تسجلها هنا
from django.utils.translation import gettext_lazy as _

# إلغاء تسجيل UserAdmin الافتراضي أولاً
admin.site.unregister(User) # <--- هذا السطر مهم جداً

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('الملف الشخصي')
    fk_name = 'user'
    fields = ('dark_mode_enabled', 'pomodoro_work_duration', 'pomodoro_short_break_duration', 'pomodoro_long_break_duration', 'pomodoro_sessions_before_long_break')
    # يمكنك إضافة 'extra = 0' إذا كنت لا تريد ظهور نماذج فارغة إضافية للإنشاء
    extra = 0


@admin.register(User) # الآن يمكنك تسجيل User مع الفئة المخصصة بك
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_dark_mode_status') # تم تغيير اسم الدالة
    list_select_related = ('profile',)

    @admin.display(description=_('الوضع الليلي'), boolean=True, ordering='profile__dark_mode_enabled')
    def profile_dark_mode_status(self, obj): # تم تغيير اسم الدالة ليكون أوضح
        try:
            if hasattr(obj, 'profile') and obj.profile is not None: # تحقق إضافي
                return obj.profile.dark_mode_enabled
        except UserProfile.DoesNotExist:
            return None # أو False إذا كنت تفضل ذلك كقيمة افتراضية
        return None # أو False

    # يمكنك إعادة تعريف get_form و get_fieldsets إذا أردت تخصيص الحقول المعروضة في صفحة تعديل المستخدم
    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     # يمكنك تعديل الحقول هنا
    #     # return form

    # def get_fieldsets(self, request, obj=None):
    #     fieldsets = super().get_fieldsets(request, obj)
    #     # يمكنك إضافة أو تعديل fieldsets هنا
    #     # return fieldsets


# تسجيل باقي الموديلات الخاصة بتطبيق core
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient_username', 'verb_summary', 'target_summary', 'unread', 'timestamp_display')
    list_filter = ('unread', 'timestamp', ('recipient', admin.RelatedOnlyFieldListFilter))
    search_fields = ('recipient__username', 'verb', 'description')
    raw_id_fields = ('recipient',)
    list_select_related = ('recipient', 'actor_content_type', 'target_content_type')
    readonly_fields = ('timestamp', 'actor', 'target')

    @admin.display(description=_('المستلم'), ordering='recipient__username')
    def recipient_username(self, obj):
        return obj.recipient.username

    @admin.display(description=_('الفعل'), ordering='verb')
    def verb_summary(self, obj):
        return obj.verb[:50] + "..." if len(obj.verb) > 50 else obj.verb

    @admin.display(description=_('الهدف'))
    def target_summary(self, obj):
        if obj.target:
            return str(obj.target)[:50] + "..." if len(str(obj.target)) > 50 else str(obj.target)
        return "-"

    @admin.display(description=_('التوقيت'), ordering='timestamp')
    def timestamp_display(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M")


@admin.register(DailyQuote)
class DailyQuoteAdmin(admin.ModelAdmin):
    list_display = ('quote_text_snippet', 'author_or_source', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('quote_text', 'author_or_source')
    list_editable = ('is_active',)
    fields = ('quote_text', 'author_or_source', 'is_active')

    @admin.display(description=_('الاقتباس'), ordering='quote_text')
    def quote_text_snippet(self, obj):
        return obj.quote_text[:70] + "..." if len(obj.quote_text) > 70 else obj.quote_text


@admin.register(EducationalResource)
class EducationalResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'link')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fields = ('title', 'description', 'link', 'is_active')

