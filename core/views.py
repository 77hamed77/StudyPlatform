from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, ListView as GenericListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import random
import json
from django.db.models import Count, Avg, Q, F # استيراد Q و F
from django.views.decorators.http import require_POST
from django.utils import timezone
import re # لاستخدام التعبيرات العادية لتنظيف النصوص
from collections import defaultdict # لاستخدام defaultdict لجمع البيانات
from datetime import timedelta

from .forms import CustomUserCreationForm, UserProfileForm, UserUpdateForm, \
    DiscussionPostForm, DiscussionCommentForm, AcademicProgressForm, \
    EducationalResourceRatingForm
from .models import UserProfile, Notification, DailyQuote, EducationalResource, \
    DiscussionPost, DiscussionComment, FAQItem, AcademicProgress, \
    EducationalResourceRating, UserFavoriteResource
from achievements.models import UserBadge
from tasks.models import Task
from files_manager.models import UserFileInteraction, Subject, MainFile # Import MainFile for AI notifications

# Simple list of Arabic stop words (can be expanded)
ARABIC_STOP_WORDS = set([
    "و", "في", "من", "إلى", "على", "عن", "مع", "أو", "أن", "لا", "ب", "ك", "ل", "هذا", "هذه", "هو", "هي", "هم", "هن",
    "الذي", "التي", "الذين", "اللاتي", "أين", "كيف", "متى", "ماذا", "لماذا", "هل", "قد", "لقد", "ثم", "إذ", "إذا",
    "كل", "بعض", "غير", "بين", "فوق", "تحت", "أمام", "خلف", "جانب", "داخل", "خارج", "عند", "قبل", "بعد", "دون",
    "مثل", "كأن", "لكن", "لكي", "حتى", "إلا", "أجل", "أي", "أيها", "أيتها", "أولئك", "أولاء", "أولى", "إياك", "إياكما",
    "إياكم", "إياكن", "إيانا", "إياه", "إياها", "إياهم", "إياهما", "إياكن", "إياي", "إلى", "أم", "أما", "أنى", "إن",
    "إنا", "أنت", "أنتم", "أنتما", "أنتن", "أنى", "أولئك", "أولاء", "أولى", "أي", "أين", "أيما", "إيه", "بئس", "بينما",
    "تلك", "ثم", "حاشا", "حتى", "حيث", "حين", "دون", "ذا", "ذات", "ذو", "ذي", "ذين", "ذوات", "ذه", "رب", "ربما",
    "ره", "سوف", "سوى", "شتان", "ص", "صه", "ض", "طالما", "عدا", "عسى", "عل", "عن", "عند", "غير", "ف", "فإن", "فقط",
    "في", "قد", "كأن", "كان", "كلا", "كلتا", "كلما", "كي", "كيف", "لا", "لعل", "لم", "لما", "لن", "لو", "لولا",
    "لوما", "ليس", "ليست", "ما", "ماذا", "متى", "مذ", "من", "منذ", "مه", "مهما", "نعم", "نحو", "نعم", "هذه", "هكذا",
    "هنا", "هناك", "هو", "هي", "و", "وإذ", "وإذا", "وإن", "والله", "وحين", "وي", "يا", "يوم", "أيضا"
])

def clean_text(text):
    """
    Cleans text by removing punctuation, numbers, and converting to lowercase.
    """
    if not text:
        return ""
    # Remove punctuation and numbers
    text = re.sub(r'[^\w\s]', '', text) # Keep letters, numbers, and spaces
    text = re.sub(r'\d+', '', text) # Remove numbers
    # Convert to lowercase (for better matching, though Arabic is not case-sensitive)
    text = text.lower()
    return text

def get_recommended_resources_for_user(user, limit=5):
    """
    Suggests educational resources to the user based on a mix of content-based filtering
    and elements of collaborative filtering (user and item similarity).
    """
    if not user.is_authenticated:
        # For unauthenticated users, show the latest active resources
        return EducationalResource.objects.filter(is_active=True).order_by('-created_at')[:limit]

    # 1. Collect resources the user has favorited or rated highly
    # This is the user's primary "basket" of preferences
    user_liked_resources_ids = set(
        UserFavoriteResource.objects.filter(user=user).values_list('resource_id', flat=True)
    )
    user_liked_resources_ids.update(
        EducationalResourceRating.objects.filter(user=user, rating__gte=4).values_list('resource_id', flat=True)
    )

    # 2. Identify resources the user has already interacted with (to avoid recommending them again)
    # Includes favorited, rated, or files interacted with
    interacted_resource_ids = set(user_liked_resources_ids)
    interacted_resource_ids.update(
        UserFileInteraction.objects.filter(user=user).values_list('resource_id', flat=True)
    )

    # If the user has no interactions, show the latest active resources
    if not user_liked_resources_ids:
        return EducationalResource.objects.filter(is_active=True).exclude(id__in=list(interacted_resource_ids)).order_by('-created_at')[:limit]

    # Fetch resource objects that the user liked
    user_liked_resources = EducationalResource.objects.filter(id__in=list(user_liked_resources_ids))

    # --- Phase 1: Content-Based Filtering ---
    # Extract keywords from user preferences
    user_keywords = set()
    for resource in user_liked_resources:
        cleaned_title = clean_text(resource.title)
        cleaned_description = clean_text(resource.description)
        user_keywords.update(word for word in cleaned_title.split() if word and word not in ARABIC_STOP_WORDS)
        user_keywords.update(word for word in cleaned_description.split() if word and word not in ARABIC_STOP_WORDS)
    
    # Initialize dictionary to store scores of candidate resources
    # Key: resource_id, Value: (score, resource_object)
    recommended_scores = {}

    # Search for resources based on keywords (Content-Based)
    if user_keywords:
        # Find other active resources the user hasn't interacted with yet
        potential_content_based_resources = EducationalResource.objects.filter(
            is_active=True
        ).exclude(
            id__in=list(interacted_resource_ids)
        ).annotate(
            avg_rating=Avg('ratings__rating'),
            num_ratings=Count('ratings')
        )

        for resource in potential_content_based_resources:
            resource_text = clean_text(resource.title + " " + (resource.description or ""))
            resource_words = set(word for word in resource_text.split() if word and word not in ARABIC_STOP_WORDS)
            
            match_score = len(user_keywords.intersection(resource_words))
            
            if match_score > 0: # Only if there's a keyword match
                # Weight by overall average rating of the resource
                rating_score = (resource.avg_rating or 0) * 0.5
                total_score = match_score * 2 + rating_score # Higher weight for text matching
                
                if resource.id not in recommended_scores or total_score > recommended_scores[resource.id][0]:
                    recommended_scores[resource.id] = (total_score, resource)

    # --- Phase 2: User-Similarity Inspired Filtering ---
    # Idea: Find other users who have common favorited/highly-rated resources with the current user.
    # Then suggest resources they liked that the current user hasn't interacted with.
    
    # Find users who favorited or rated the same resources as the current user
    # (at least one common resource)
    similar_users_ids = UserFavoriteResource.objects.filter(
        resource__id__in=list(user_liked_resources_ids)
    ).exclude(
        user=user
    ).values_list('user_id', flat=True).distinct()

    similar_users_ids_from_ratings = EducationalResourceRating.objects.filter(
        resource__id__in=list(user_liked_resources_ids),
        rating__gte=4 # Consider only high ratings
    ).exclude(
        user=user
    ).values_list('user_id', flat=True).distinct()

    all_similar_users_ids = list(set(list(similar_users_ids) + list(similar_users_ids_from_ratings)))

    if all_similar_users_ids:
        # Fetch resources favored/highly rated by these similar users
        resources_from_similar_users = EducationalResource.objects.filter(is_active=True).filter(
            Q(favorited_by__user__id__in=all_similar_users_ids) |
            Q(ratings__user__id__in=all_similar_users_ids, ratings__rating__gte=4)
        ).exclude(
            id__in=list(interacted_resource_ids)
        ).annotate(
            avg_rating=Avg('ratings__rating'),
            num_ratings=Count('ratings')
        ).distinct() # Ensure no duplicate resources

        for resource in resources_from_similar_users:
            # Can give lower weight to these recommendations compared to direct content match
            score = (resource.avg_rating or 0) * 0.75 # Lower weight
            if resource.id not in recommended_scores or score > recommended_scores[resource.id][0]:
                recommended_scores[resource.id] = (score, resource)

    # --- Phase 3: Item-Similarity Inspired Filtering ---
    # Idea: If the user liked resources X and Y, find resources that frequently appear with X and Y
    # in other users' preferences.

    # Collect all interactions (favorites and high ratings) from all users
    all_favorites = UserFavoriteResource.objects.all().values('user_id', 'resource_id')
    all_high_ratings = EducationalResourceRating.objects.filter(rating__gte=4).values('user_id', 'resource_id')

    user_resource_map = defaultdict(set)
    for entry in all_favorites:
        user_resource_map[entry['user_id']].add(entry['resource_id'])
    for entry in all_high_ratings:
        user_resource_map[entry['user_id']].add(entry['resource_id'])

    # Build item similarity matrix (simplified)
    # item_pair_counts[(item1, item2)] = number of users who interacted with both
    item_pair_counts = defaultdict(int)
    for user_id, resources_set in user_resource_map.items():
        resources_list = sorted(list(resources_set)) # Ensure consistent order for pairs
        for i in range(len(resources_list)):
            for j in range(i + 1, len(resources_list)):
                item1, item2 = resources_list[i], resources_list[j]
                item_pair_counts[(item1, item2)] += 1
                item_pair_counts[(item2, item1)] += 1 # Order doesn't matter

    # Recommend resources based on item similarity
    for liked_resource_id in user_liked_resources_ids:
        for (item1, item2), count in item_pair_counts.items():
            if item1 == liked_resource_id and item2 not in interacted_resource_ids:
                # The more users who liked both resources, the higher the recommendation score
                # More complex similarity measures (e.g., Jaccard, Cosine) could be used here
                score = count * 0.1 # Relatively low weight
                
                # Fetch resource object if not already present
                if item2 not in recommended_scores:
                    try:
                        resource = EducationalResource.objects.get(id=item2, is_active=True)
                        resource.avg_rating = resource.average_rating # Load properties
                        resource.num_ratings = resource.total_ratings
                        recommended_scores[item2] = (score, resource)
                    except EducationalResource.DoesNotExist:
                        continue # Skip non-existent or inactive resources
                else:
                    # Update score if new score is higher
                    current_score, current_resource = recommended_scores[item2]
                    if score > current_score:
                        recommended_scores[item2] = (score, current_resource)


    # 4. Aggregate and sort recommended resources
    final_recommendations_list = sorted(
        recommended_scores.values(),
        key=lambda x: x[0], # Sort by match score
        reverse=True
    )

    # Return top N resources
    # Ensure only resource objects are returned
    return [res_obj for score, res_obj in final_recommendations_list][:limit]


class HomePageView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('core:dashboard')
    template_name = 'registration/signup.html'
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "تم إنشاء حسابك بنجاح!")
        return redirect(self.success_url)

class UserSettingsView(LoginRequiredMixin, View):
    template_name = 'core/settings.html'

    def get(self, request, *args, **kwargs):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
        return render(request, self.template_name, {'user_form': user_form, 'profile_form': profile_form})

    def post(self, request, *args, **kwargs):
        # Handle theme update via AJAX separately
        if request.POST.get('update_theme_only') == 'true' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            is_dark_mode = request.POST.get('dark_mode_enabled') == 'on'
            profile = request.user.profile
            profile.dark_mode_enabled = is_dark_mode
            profile.save(update_fields=['dark_mode_enabled'])
            return JsonResponse({'status': 'success', 'dark_mode_enabled': is_dark_mode})
        
        # Handle dashboard layout preferences update via AJAX
        if request.POST.get('update_dashboard_layout') == 'true' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                visible_sections = json.loads(request.POST.get('visible_sections', '[]'))
                section_order = json.loads(request.POST.get('section_order', '[]'))
                
                profile = request.user.profile
                profile.dashboard_layout_preferences = {
                    'visible_sections': visible_sections,
                    'section_order': section_order
                }
                profile.save(update_fields=['dashboard_layout_preferences'])
                return JsonResponse({'status': 'success', 'message': 'تم حفظ تفضيلات لوحة التحكم بنجاح.'})
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'بيانات JSON غير صالحة لتفضيلات لوحة التحكم.'}, status=400)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'حدث خطأ أثناء حفظ تفضيلات لوحة التحكم: {str(e)}'}, status=500)


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
        user = self.request.user

        # Fetch Daily Quote
        active_quotes = DailyQuote.objects.filter(is_active=True)
        if active_quotes.exists():
            count = active_quotes.count()
            random_index = random.randint(0, count - 1)
            context['daily_quote'] = active_quotes[random_index]
        else:
            context['daily_quote'] = None

        # Fetch Latest News
        try:
            from news.models import NewsItem
            context['latest_news'] = NewsItem.objects.filter(is_important=True).order_by('-publication_date')[:3]
        except Exception:
            context['latest_news'] = None

        # Fetch Upcoming Tasks
        try:
            context['upcoming_tasks'] = Task.objects.filter(
                user=user,
                status__in=['pending', 'in_progress']
            ).order_by('due_date')[:3]
        except Exception:
            context['upcoming_tasks'] = None
        
        # Add Recommended Resources
        context['recommended_resources'] = get_recommended_resources_for_user(user, limit=4)

        # Get Dashboard Layout Preferences
        user_profile = user.profile
        default_sections = {
            'tasks_card': {'title': _("مهامك القادمة"), 'icon': 'fas fa-tasks', 'url': str(reverse_lazy('tasks:task_list'))},
            'news_card': {'title': _("آخر الأخبار الهامة"), 'icon': 'fas fa-bullhorn', 'url': str(reverse_lazy('news:news_list'))},
            'academic_progress_card': {'title': _("تقدمك الأكاديمي"), 'icon': 'fas fa-chart-line', 'url': str(reverse_lazy('core:academic_progress'))},
            'educational_resources_card': {'title': _("الموارد التعليمية"), 'icon': 'fas fa-book-open', 'url': str(reverse_lazy('core:educational_resources'))},
            'discussion_board_card': {'title': _("لوحة المناقشات"), 'icon': 'fas fa-comments', 'url': str(reverse_lazy('core:discussion_board'))},
            'tools_card': {'title': _("أدوات مفيدة"), 'icon': 'fas fa-tools', 'url_calculator': str(reverse_lazy('core:scientific_calculator')), 'url_converter': str(reverse_lazy('core:unit_converter'))},
            'recommendations_section': {'title': _("موارد موصى بها لك"), 'icon': 'fas fa-lightbulb'},
        }
        
        # Pass the raw dictionary for the Django template loop in the customization panel
        context['all_available_sections_raw'] = default_sections 

        # Pass default_sections as a JSON string to the context
        context['all_available_sections_json'] = json.dumps(default_sections, ensure_ascii=False)
        
        return context

    def _check_and_create_ai_notifications(self, user):
        """
        Checks for conditions to create AI-driven notifications based on user behavior.
        Examples:
        - Remind user to review a subject if no interaction for a long time.
        - Remind user about upcoming deadlines if tasks are pending.
        """
        now = timezone.now()
        
        # --- Notification 1: Remind to review subjects not interacted with recently ---
        # Define what "long time" means (e.g., 30 days)
        inactivity_threshold = timedelta(days=30)
        
        # Get all subjects the user has tasks or file interactions for
        user_subjects_from_tasks = Task.objects.filter(user=user, subject__isnull=False).values_list('subject', flat=True).distinct()
        user_subjects_from_files = UserFileInteraction.objects.filter(user=user, file__subject__isnull=False).values_list('file__subject', flat=True).distinct()
        
        all_user_subject_ids = list(set(list(user_subjects_from_tasks) + list(user_subjects_from_files)))
        
        for subject_id in all_user_subject_ids:
            subject = Subject.objects.get(pk=subject_id)
            
            # Find last interaction for this subject (task completion or file interaction)
            last_task_completion = Task.objects.filter(user=user, subject=subject, status='completed').order_by('-updated_at').first()
            last_file_interaction = UserFileInteraction.objects.filter(user=user, file__subject=subject).order_by('-last_accessed').first()
            
            last_interaction_time = None
            if last_task_completion:
                last_interaction_time = last_task_completion.updated_at
            if last_file_interaction and (not last_interaction_time or last_file_interaction.last_accessed > last_interaction_time):
                last_interaction_time = last_file_interaction.last_accessed
            
            if last_interaction_time:
                time_since_last_interaction = now - last_interaction_time
                if time_since_last_interaction > inactivity_threshold:
                    # Check if a similar notification has been sent recently (e.g., in the last 7 days)
                    recent_notification_exists = Notification.objects.filter(
                        recipient=user,
                        verb=_("تذكير بمراجعة مادة"),
                        target_content_type=ContentType.objects.get_for_model(Subject),
                        target_object_id=subject.pk,
                        timestamp__gte=now - timedelta(days=7)
                    ).exists()

                    if not recent_notification_exists:
                        Notification.objects.create(
                            recipient=user,
                            verb=_("تذكير بمراجعة مادة"),
                            description=f"{_('لم تقم بمراجعة مادة')} '{subject.name}' {_('منذ فترة. قد يكون الوقت مناسباً للمراجعة!')}",
                            target_content_type=ContentType.objects.get_for_model(Subject),
                            target_object_id=subject.pk,
                            metadata={'reason': 'inactivity', 'last_interaction': last_interaction_time.isoformat()}
                        )
                        print(f"AI Notification: User {user.username} reminded to review {subject.name}")

        # --- Notification 2: Remind about overdue tasks (if any) ---
        overdue_tasks = Task.objects.filter(user=user, due_date__lt=now.date(), status__in=['pending', 'in_progress'])
        if overdue_tasks.exists():
            # Check if an overdue task reminder has been sent today
            recent_notification_exists = Notification.objects.filter(
                recipient=user,
                verb=_("تذكير بمهام متأخرة"),
                timestamp__date=now.date()
            ).exists()

            if not recent_notification_exists:
                num_overdue = overdue_tasks.count()
                Notification.objects.create(
                    recipient=user,
                    verb=_("تذكير بمهام متأخرة"),
                    description=f"{_('لديك')} {num_overdue} {_('مهام متأخرة. يرجى مراجعتها!')}",
                    metadata={'reason': 'overdue_tasks', 'count': num_overdue}
                )
                print(f"AI Notification: User {user.username} reminded about {num_overdue} overdue tasks.")

        # --- Notification 3: Suggest exploring new resources based on academic progress (e.g., low grade in a subject) ---
        # This is a more complex AI notification that might require LLM interaction or more sophisticated logic
        # For demonstration, let's say if a user has a low grade in a subject, suggest related resources.
        low_grade_threshold = 60.0 # Example threshold
        recent_academic_progress = AcademicProgress.objects.filter(
            user=user,
            grade__lt=low_grade_threshold,
            date_recorded__gte=now.date() - timedelta(days=90) # Check recent grades (last 3 months)
        ).select_related('subject').distinct('subject') # Get unique subjects with low grades recently

        for progress_entry in recent_academic_progress:
            subject = progress_entry.subject
            if subject:
                # Check if a similar notification has been sent recently for this subject
                recent_notification_exists = Notification.objects.filter(
                    recipient=user,
                    verb=_("اقتراح موارد دراسية"),
                    target_content_type=ContentType.objects.get_for_model(Subject),
                    target_object_id=subject.pk,
                    timestamp__gte=now - timedelta(days=14) # Don't spam
                ).exists()

                if not recent_notification_exists:
                    Notification.objects.create(
                        recipient=user,
                        verb=_("اقتراح موارد دراسية"),
                        description=f"{_('لاحظنا أنك قد تواجه صعوبة في مادة')} '{subject.name}'. {_('قد تساعدك بعض الموارد الإضافية!')}",
                        metadata={'reason': 'low_grade', 'subject_id': subject.pk, 'grade': float(progress_entry.grade)}
                    )
                    print(f"AI Notification: User {user.username} suggested resources for {subject.name} due to low grade.")


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
        context['tasks_completion_labels_raw'] = [d.strftime('%Y-%m-%d') for d in days_range_raw]
        context['tasks_completion_data_raw'] = completed_tasks_per_per_day_raw
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
            # Mark all unread notifications as read when viewing the list page
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


class EducationalResourcesView(GenericListView):
    """
    View a list of educational resources with ratings and favorites support.
    """
    model = EducationalResource
    template_name = 'core/educational_resources.html'
    context_object_name = 'resources'
    paginate_by = 10
    
    def get_queryset(self):
        # Fetch active resources only, with average rating and number of ratings
        queryset = EducationalResource.objects.filter(is_active=True).annotate(
            avg_rating=Avg('ratings__rating'),
            num_ratings=Count('ratings')
        ).order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Get current user's rating for each resource
            user_ratings = EducationalResourceRating.objects.filter(user=self.request.user)
            context['user_ratings_map'] = {rating.resource_id: rating for rating in user_ratings}
            
            # Get current user's favorite resources
            favorite_resources = UserFavoriteResource.objects.filter(user=self.request.user).values_list('resource_id', flat=True)
            context['user_favorite_resources'] = list(favorite_resources)

            # New rating form (can be used in a modal or hidden part)
            context['rating_form'] = EducationalResourceRatingForm()
        return context

    def post(self, request, *args, **kwargs):
        # Handle rating submission
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)

        resource_id = request.POST.get('resource_id')
        if not resource_id:
            return JsonResponse({'status': 'error', 'message': 'Resource ID is missing'}, status=400)
        
        resource = get_object_or_404(EducationalResource, pk=resource_id)
        
        form = EducationalResourceRatingForm(request.POST)
        if form.is_valid():
            rating_value = form.cleaned_data['rating']
            review_text = form.cleaned_data['review_text']

            # Try to update existing rating or create a new one
            rating_obj, created = EducationalResourceRating.objects.update_or_create(
                resource=resource,
                user=request.user,
                defaults={'rating': rating_value, 'review_text': review_text}
            )
            
            if created:
                messages.success(request, "تم إضافة تقييمك بنجاح!")
            else:
                messages.success(request, "تم تحديث تقييمك بنجاح!")
            
            # You can redirect or return JsonResponse for AJAX
            return redirect('core:educational_resources') # Or JsonResponse({'status': 'success', 'message': 'Rating saved'})
        else:
            messages.error(request, "حدث خطأ في التقييم. يرجى التحقق من البيانات.")
            # If form is invalid, re-render the page with errors
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            context['rating_form'] = form # Return form with errors
            return render(request, self.template_name, context)


@login_required
@require_POST
def toggle_favorite_resource(request):
    """
    Toggle favorite status for an educational resource via AJAX.
    """
    resource_id = request.POST.get('resource_id')
    if not resource_id:
        return JsonResponse({'status': 'error', 'message': 'Resource ID is missing'}, status=400)
    
    resource = get_object_or_404(EducationalResource, pk=resource_id)
    
    favorite, created = UserFavoriteResource.objects.get_or_create(
        user=request.user,
        resource=resource
    )

    if not created:
        # If already exists, delete it (remove from favorites)
        favorite.delete()
        return JsonResponse({'status': 'removed', 'message': 'تمت إزالة المورد من المفضلة.'})
    else:
        # If just created, it means it was added to favorites
        return JsonResponse({'status': 'added', 'message': 'تمت إضافة المورد إلى المفضلة.'})


class UserFavoriteResourcesListView(LoginRequiredMixin, GenericListView):
    """
    View a list of the current user's favorite educational resources.
    """
    model = UserFavoriteResource
    template_name = 'core/favorite_resources.html'
    context_object_name = 'favorite_entries'
    paginate_by = 10

    def get_queryset(self):
        # Fetch current user's favorite resources only
        # select_related('resource') to load resource data to avoid extra queries
        return UserFavoriteResource.objects.filter(user=self.request.user).select_related('resource').order_by('-added_at')


# --- New views for Tools and Utilities (from previous update) ---

class ScientificCalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'core/scientific_calculator.html'

class UnitConverterView(LoginRequiredMixin, TemplateView):
    template_name = 'core/unit_converter.html'

class FAQListView(LoginRequiredMixin, GenericListView):
    model = FAQItem
    template_name = 'core/faq_list.html'
    context_object_name = 'faqs'
    paginate_by = 10

    def get_queryset(self):
        return FAQItem.objects.filter(is_active=True).order_by('order')


class DiscussionBoardListView(LoginRequiredMixin, GenericListView):
    model = DiscussionPost
    template_name = 'core/discussion_board.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return DiscussionPost.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DiscussionPostForm()
        return context

    def post(self, request, *args, **kwargs):
        form = DiscussionPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "تم نشر موضوعك بنجاح!")
            return redirect('core:discussion_board')
        else:
            messages.error(request, "حدث خطأ أثناء نشر الموضوع. يرجى التحقق من البيانات.")
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class DiscussionPostDetailView(LoginRequiredMixin, DetailView):
    model = DiscussionPost
    template_name = 'core/discussion_post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['comment_form'] = DiscussionCommentForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        comment_form = DiscussionCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = self.object
            comment.author = request.user
            comment.save()
            messages.success(request, "تم إضافة تعليقك بنجاح!")
            return redirect(self.object.get_absolute_url())
        else:
            messages.error(request, "حدث خطأ أثناء إضافة التعليق. يرجى التحقق من البيانات.")
            context = self.get_context_data()
            context['comment_form'] = comment_form
            return render(request, self.template_name, context)


class AcademicProgressView(LoginRequiredMixin, GenericListView):
    model = AcademicProgress
    template_name = 'core/academic_progress.html'
    context_object_name = 'progress_entries'
    paginate_by = 10

    def get_queryset(self):
        return AcademicProgress.objects.filter(user=self.request.user).order_by('-date_recorded', 'subject__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AcademicProgressForm(initial={'user': self.request.user})
        
        avg_grades = AcademicProgress.objects.filter(user=self.request.user, grade__isnull=False) \
            .values('subject__name') \
            .annotate(avg_grade=Avg('grade')) \
            .order_by('subject__name')
        
        context['chart_labels'] = [entry['subject__name'] for entry in avg_grades]
        context['chart_data'] = [float(entry['avg_grade']) for entry in avg_grades]
        
        return context

    def post(self, request, *args, **kwargs):
        form = AcademicProgressForm(request.POST)
        if form.is_valid():
            progress_entry = form.save(commit=False)
            progress_entry.user = request.user
            progress_entry.save()
            messages.success(request, "تم تسجيل تقدمك الأكاديمي بنجاح!")
            return redirect('core:academic_progress')
        else:
            messages.error(request, "حدث خطأ أثناء تسجيل التقدم. يرجى التحقق من البيانات.")
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)

