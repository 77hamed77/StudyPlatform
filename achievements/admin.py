from django.contrib import admin
from .models import Badge, UserBadge, UserAchievementStats, XPTransaction, StudyChallenge, UserStudyChallenge
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count # For aggregate functions in admin


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
        return obj.earned_by_users.count()


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'badge_name', 'earned_at_display')
    list_filter = ('badge', 'earned_at', ('user', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__username', 'badge__name')
    autocomplete_fields = ['user', 'badge']
    readonly_fields = ('earned_at',)

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description=_('الشارة'), ordering='badge__name')
    def badge_name(self, obj):
        return obj.badge.name

    @admin.display(description=_('تاريخ الاكتساب'), ordering='earned_at')
    def earned_at_display(self, obj):
        return obj.earned_at.strftime("%Y-%m-%d %H:%M")


# --- New Admin Classes for Gamification Models ---

@admin.register(UserAchievementStats)
class UserAchievementStatsAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'total_xp', 'level', 'last_xp_update')
    search_fields = ('user__username',)
    list_filter = ('level',)
    readonly_fields = ('user', 'total_xp', 'level', 'last_xp_update') # XP and Level are updated by signals/methods
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('إحصائيات التقدم'), {
            'fields': ('total_xp', 'level', 'last_xp_update')
        }),
    )

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'amount', 'activity', 'timestamp', 'related_object')
    list_filter = ('activity', 'timestamp', ('user', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__username', 'activity', 'amount')
    readonly_fields = ('user', 'amount', 'activity', 'timestamp', 'content_type', 'object_id', 'content_object')

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description=_('الكائن المرتبط'))
    def related_object(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return "-"


@admin.register(StudyChallenge)
class StudyChallengeAdmin(admin.ModelAdmin):
    list_display = ('name', 'challenge_type', 'target_value', 'xp_reward', 'badge_reward', 'start_date', 'end_date', 'is_active', 'is_current', 'is_upcoming', 'is_past')
    list_filter = ('challenge_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description', 'challenge_type')
    date_hierarchy = 'start_date'
    raw_id_fields = ('badge_reward',) # Use raw_id_fields for ForeignKey to avoid large dropdowns

    @admin.display(description=_('نشط حالياً'))
    def is_current(self, obj):
        return obj.is_current
    is_current.boolean = True

    @admin.display(description=_('قادم'))
    def is_upcoming(self, obj):
        return obj.is_upcoming
    is_upcoming.boolean = True

    @admin.display(description=_('منتهي'))
    def is_past(self, obj):
        return obj.is_past
    is_past.boolean = True


@admin.register(UserStudyChallenge)
class UserStudyChallengeAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'challenge_name', 'current_progress', 'completed', 'joined_at', 'completed_at')
    list_filter = ('completed', 'challenge', 'joined_at', ('user', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__username', 'challenge__name')
    readonly_fields = ('user', 'challenge', 'joined_at', 'completed_at') # Progress is updated by signals/methods
    raw_id_fields = ('user', 'challenge')

    @admin.display(description=_('المستخدم'), ordering='user__username')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description=_('التحدي'), ordering='challenge__name')
    def challenge_name(self, obj):
        return obj.challenge.name

