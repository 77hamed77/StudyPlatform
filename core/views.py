from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, ListView as GenericListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm, UserProfileForm, UserUpdateForm
from .models import UserProfile, Notification, DailyQuote
from achievements.models import UserBadge
from tasks.models import Task
from files_manager.models import UserFileInteraction
from django.db.models import Count
from django.utils import timezone
import json
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import random
from news.models import NewsItem
from django.views.decorators.http import require_POST

# ... (HomePageView, SignUpView كما هي من قبل) ...
class HomePageView(TemplateView):
    template_name = 'core/home.html'

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('core:dashboard')
    template_name = 'registration/signup.html'
    def form_valid(self, form):
        user = form.save(); login(self.request, user)
        messages.success(self.request, "تم إنشاء حسابك بنجاح!")
        return redirect(self.success_url)

class UserSettingsView(LoginRequiredMixin, View):
    template_name = 'core/settings.html'

    def get(self, request, *args, **kwargs):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
        return render(request, self.template_name, {'user_form': user_form, 'profile_form': profile_form})

    def post(self, request, *args, **kwargs):
        if request.POST.get('update_theme_only') == 'true' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            is_dark_mode = request.POST.get('dark_mode_enabled') == 'on'
            profile = request.user.profile
            profile.dark_mode_enabled = is_dark_mode
            profile.save(update_fields=['dark_mode_enabled'])
            return JsonResponse({'status': 'success', 'dark_mode_enabled': is_dark_mode})

        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'تم تحديث إعداداتك بنجاح!')
            return redirect('core:settings')
        else:
            if not user_form.is_valid():
                messages.error(request, 'يرجى تصحيح الأخطاء في معلومات المستخدم.')
            if not profile_form.is_valid():
                messages.error(request, 'يرجى تصحيح الأخطاء في إعدادات العرض والمؤقت.')
        return render(request, self.template_name, {'user_form': user_form, 'profile_form': profile_form})

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_quotes = DailyQuote.objects.filter(is_active=True)
        if active_quotes.exists():
            count = active_quotes.count()
            random_index = random.randint(0, count - 1)
            context['daily_quote'] = active_quotes[random_index]
        else:
            context['daily_quote'] = None
        try:
            context['latest_news'] = NewsItem.objects.filter(is_important=True).order_by('-publication_date')[:3]
        except Exception:
            context['latest_news'] = None
        try:
            context['upcoming_tasks'] = Task.objects.filter(
                user=self.request.user,
                status__in=['pending', 'in_progress']
            ).order_by('due_date')[:3]
        except Exception:
            context['upcoming_tasks'] = None
        return context

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'core/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['earned_badges'] = UserBadge.objects.filter(user=user).select_related('badge')
        today = timezone.now().date()
        days_range_raw = [today - timezone.timedelta(days=i) for i in range(6, -1, -1)]
        completed_tasks_per_day_raw = []
        for day in days_range_raw:
            count = Task.objects.filter(user=user, status='completed', updated_at__date=day).count()
            completed_tasks_per_day_raw.append(count)
        context['tasks_completion_labels_raw'] = [d.strftime('%Y-%m-%d') for d in days_range_raw]  # تنسيق صريح
        context['tasks_completion_data_raw'] = completed_tasks_per_day_raw
        tasks_by_subject_raw = list(Task.objects.filter(user=user, status='completed', subject__isnull=False).values('subject__name').annotate(count=Count('id')).order_by('-count'))
        context['tasks_by_subject_raw'] = tasks_by_subject_raw
        context['total_tasks_completed'] = Task.objects.filter(user=user, status='completed').count()
        context['total_tasks_pending'] = Task.objects.filter(user=user, status__in=['pending', 'in_progress']).count()
        context['files_marked_as_read_count'] = UserFileInteraction.objects.filter(user=user, marked_as_read=True).count()
        return context

@method_decorator(login_required, name='dispatch')
class NotificationListView(GenericListView):
    model = Notification
    template_name = 'core/notifications_list.html'
    context_object_name = 'notifications_list'
    paginate_by = 10
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-timestamp')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notification_to_mark_read_id = self.request.GET.get('mark_read')
        if notification_to_mark_read_id:
            try:
                notif_to_mark = Notification.objects.get(pk=notification_to_mark_read_id, recipient=self.request.user, unread=True)
                notif_to_mark.mark_as_read()
            except (Notification.DoesNotExist, ValueError):
                pass
        if not notification_to_mark_read_id:
            Notification.objects.filter(recipient=self.request.user, unread=True).update(unread=False)
        return context

@require_POST
def mark_all_notifications_read(request):
    if request.user.is_authenticated:
        Notification.objects.filter(recipient=request.user, unread=True).update(unread=False)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)

def mark_notification_read(request):
    if request.user.is_authenticated and 'id' in request.GET:
        try:
            notification = Notification.objects.get(id=request.GET['id'], recipient=request.user)
            if notification.unread:
                notification.mark_as_read()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            pass
    return JsonResponse({'status': 'error'}, status=400)