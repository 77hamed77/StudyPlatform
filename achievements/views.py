from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Sum, Count # Import F and Sum for annotations
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Badge, UserBadge, UserAchievementStats, StudyChallenge, UserStudyChallenge, XPTransaction


class UserAchievementsView(LoginRequiredMixin, TemplateView):
    """
    يعرض شارات المستخدم، نقاط الخبرة، والمستوى.
    """
    template_name = 'achievements/user_achievements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's earned badges
        context['earned_badges'] = UserBadge.objects.filter(user=user).select_related('badge').order_by('-earned_at')

        # Get user's achievement stats (XP and Level)
        user_stats, created = UserAchievementStats.objects.get_or_create(user=user)
        context['user_stats'] = user_stats

        # Get user's recent XP transactions
        context['recent_xp_transactions'] = XPTransaction.objects.filter(user=user).order_by('-timestamp')[:5]

        context['page_title'] = _("إنجازاتي")
        return context


class AllBadgesListView(LoginRequiredMixin, ListView):
    """
    يعرض قائمة بجميع الشارات المتاحة (سواء تم اكتسابها أم لا).
    """
    model = Badge
    template_name = 'achievements/all_badges_list.html'
    context_object_name = 'all_badges'
    paginate_by = 12
    ordering = ['order', 'name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("جميع الشارات المتاحة")
        
        # Annotate badges with whether the current user has earned them
        if self.request.user.is_authenticated:
            earned_badge_ids = UserBadge.objects.filter(user=self.request.user).values_list('badge_id', flat=True)
            for badge in context['all_badges']:
                badge.is_earned = badge.pk in earned_badge_ids
        return context


class LeaderboardView(LoginRequiredMixin, ListView):
    """
    يعرض لوحة الصدارة بناءً على نقاط الخبرة.
    """
    model = UserAchievementStats
    template_name = 'achievements/leaderboard.html'
    context_object_name = 'leaderboard_entries'
    paginate_by = 10
    ordering = ['-total_xp', '-level', 'user__username'] # Sort by XP, then Level, then username

    def get_queryset(self):
        # Select related user to display username directly
        queryset = super().get_queryset().select_related('user')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("لوحة الصدارة")
        return context


class StudyChallengeListView(LoginRequiredMixin, ListView):
    """
    يعرض قائمة بتحديات الدراسة المتاحة (الحالية، القادمة، والمنتهية).
    """
    model = StudyChallenge
    template_name = 'achievements/study_challenge_list.html'
    context_object_name = 'challenges'
    paginate_by = 10
    ordering = ['-start_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Annotate with user's progress if logged in
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                user_progress=Sum(
                    F('participants__current_progress'),
                    filter=models.Q(participants__user=self.request.user)
                ),
                user_completed=models.Exists(
                    UserStudyChallenge.objects.filter(
                        challenge=models.OuterRef('pk'),
                        user=self.request.user,
                        completed=True
                    )
                ),
                user_joined=models.Exists(
                    UserStudyChallenge.objects.filter(
                        challenge=models.OuterRef('pk'),
                        user=self.request.user
                    )
                )
            )
        
        # Filter by active challenges by default, but allow filtering by status
        status_filter = self.request.GET.get('status')
        now = timezone.now()

        if status_filter == 'current':
            queryset = queryset.filter(start_date__lte=now, end_date__gte=now, is_active=True)
        elif status_filter == 'upcoming':
            queryset = queryset.filter(start_date__gt=now, is_active=True)
        elif status_filter == 'past':
            queryset = queryset.filter(end_date__lt=now)
        else: # Default to current and upcoming active challenges
            queryset = queryset.filter(Q(start_date__lte=now, end_date__gte=now) | Q(start_date__gt=now), is_active=True)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("تحديات الدراسة")
        context['current_status_filter'] = self.request.GET.get('status', 'all')
        return context


class StudyChallengeDetailView(LoginRequiredMixin, DetailView):
    """
    يعرض تفاصيل تحدي دراسي محدد وتقدم المستخدم فيه.
    """
    model = StudyChallenge
    template_name = 'achievements/study_challenge_detail.html'
    context_object_name = 'challenge'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = self.get_object()
        user = self.request.user

        # Get user's progress for this specific challenge
        user_challenge, created = UserStudyChallenge.objects.get_or_create(
            user=user,
            challenge=challenge
        )
        context['user_challenge'] = user_challenge
        context['page_title'] = challenge.name
        
        # Calculate percentage progress
        if challenge.target_value > 0:
            context['progress_percentage'] = min(100, (user_challenge.current_progress / challenge.target_value) * 100)
        else:
            context['progress_percentage'] = 0 # Avoid division by zero

        return context

