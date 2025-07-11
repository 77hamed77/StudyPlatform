from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Notification, DailyQuote, EducationalResource, \
    DiscussionPost, DiscussionComment, FAQItem, AcademicProgress, \
    EducationalResourceRating, UserFavoriteResource # استيراد النماذج الجديدة
from django.utils.translation import gettext_lazy as _

# إلغاء تسجيل UserAdmin الافتراضي أولاً
admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('الملف الشخصي')
    fk_name = 'user'
    fields = ('dark_mode_enabled', 'pomodoro_work_duration', 'pomodoro_short_break_duration', 'pomodoro_long_break_duration', 'pomodoro_sessions_before_long_break')
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_dark_mode_status')
    list_select_related = ('profile',)

    @admin.display(description=_('الوضع الليلي'), boolean=True, ordering='profile__dark_mode_enabled')
    def profile_dark_mode_status(self, obj):
        try:
            if hasattr(obj, 'profile') and obj.profile is not None:
                return obj.profile.dark_mode_enabled
        except UserProfile.DoesNotExist:
            return None
        return None


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
    list_display = ('title', 'link', 'is_active', 'average_rating_display', 'total_ratings', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'link')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fields = ('title', 'description', 'link', 'is_active')

    @admin.display(description=_('متوسط التقييم'), ordering='_average_rating')
    def average_rating_display(self, obj):
        return f"{obj.average_rating:.2f}" if obj.average_rating else "N/A"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # قم بإضافة حقل متوسط التقييم لتمكين الترتيب
        return queryset.annotate(_average_rating=models.Avg('ratings__rating'))


# --- تسجيل نماذج الأدوات والمرافق الجديدة (من التحديث السابق) ---

@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_display', 'created_at', 'is_anonymous')
    list_filter = ('is_anonymous', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    raw_id_fields = ('author',)
    date_hierarchy = 'created_at'

    @admin.display(description=_('الكاتب'), ordering='author__username')
    def author_display(self, obj):
        return "مجهول" if obj.is_anonymous else obj.author.username


@admin.register(DiscussionComment)
class DiscussionCommentAdmin(admin.ModelAdmin):
    list_display = ('post_title_snippet', 'author_display', 'created_at', 'is_anonymous')
    list_filter = ('is_anonymous', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    raw_id_fields = ('post', 'author',)

    @admin.display(description=_('المنشور'), ordering='post__title')
    def post_title_snippet(self, obj):
        return obj.post.title[:50] + "..." if len(obj.post.title) > 50 else obj.post.title

    @admin.display(description=_('الكاتب'), ordering='author__username')
    def author_display(self, obj):
        return "مجهول" if obj.is_anonymous else obj.author.username


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')
    fields = ('question', 'answer', 'order', 'is_active')


@admin.register(AcademicProgress)
class AcademicProgressAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'subject_name', 'grade', 'date_recorded')
    list_filter = ('date_recorded', 'subject')
    search_fields = ('user__username', 'subject__name', 'notes')
    raw_id_fields = ('user', 'subject')
    date_hierarchy = 'date_recorded'

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description=_('المادة'), ordering='subject__name')
    def subject_name(self, obj):
        return obj.subject.name if obj.subject else "-"


# --- تسجيل نماذج التقييمات والمفضلة الجديدة ---

@admin.register(EducationalResourceRating)
class EducationalResourceRatingAdmin(admin.ModelAdmin):
    list_display = ('resource_title', 'user_username', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('resource__title', 'user__username', 'review_text')
    raw_id_fields = ('resource', 'user')
    date_hierarchy = 'created_at'

    @admin.display(description=_('المورد'), ordering='resource__title')
    def resource_title(self, obj):
        return obj.resource.title

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username


@admin.register(UserFavoriteResource)
class UserFavoriteResourceAdmin(admin.ModelAdmin):
    list_display = ('resource_title', 'user_username', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('resource__title', 'user__username')
    raw_id_fields = ('resource', 'user')
    date_hierarchy = 'added_at'

    @admin.display(description=_('المورد'), ordering='resource__title')
    def resource_title(self, obj):
        return obj.resource.title

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username

