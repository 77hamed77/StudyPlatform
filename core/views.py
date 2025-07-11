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

from .forms import CustomUserCreationForm, UserProfileForm, UserUpdateForm, \
    DiscussionPostForm, DiscussionCommentForm, AcademicProgressForm, \
    EducationalResourceRatingForm
from .models import UserProfile, Notification, DailyQuote, EducationalResource, \
    DiscussionPost, DiscussionComment, FAQItem, AcademicProgress, \
    EducationalResourceRating, UserFavoriteResource
from achievements.models import UserBadge
from tasks.models import Task
from files_manager.models import UserFileInteraction, Subject

# قائمة بسيطة للكلمات المتوقفة باللغة العربية (يمكن توسيعها)
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
    ينظف النص بإزالة علامات الترقيم والأرقام وتحويله إلى حروف صغيرة.
    """
    if not text:
        return ""
    # إزالة علامات الترقيم والأرقام
    text = re.sub(r'[^\w\s]', '', text) # إبقاء الحروف والأرقام والمسافات
    text = re.sub(r'\d+', '', text) # إزالة الأرقام
    # تحويل إلى حروف صغيرة (للتطابق الأفضل، على الرغم من أن العربية لا تفرق في الحالة)
    text = text.lower()
    return text

def get_recommended_resources_for_user(user, limit=5):
    """
    يقترح موارد تعليمية للمستخدم بناءً على مزيج من التصفية المستندة إلى المحتوى
    وعناصر من التصفية التعاونية (تشابه المستخدمين والعناصر).
    """
    if not user.is_authenticated:
        # للمستخدمين غير المسجلين، أظهر أحدث الموارد النشطة
        return EducationalResource.objects.filter(is_active=True).order_by('-created_at')[:limit]

    # 1. جمع الموارد التي فضلها المستخدم أو قيمها عالياً
    # هذه هي "سلة" تفضيلات المستخدم الأساسية
    user_liked_resources_ids = set(
        UserFavoriteResource.objects.filter(user=user).values_list('resource_id', flat=True)
    )
    user_liked_resources_ids.update(
        EducationalResourceRating.objects.filter(user=user, rating__gte=4).values_list('resource_id', flat=True)
    )

    # 2. تحديد الموارد التي تفاعل معها المستخدم بالفعل (لعدم التوصية بها مرة أخرى)
    # تشمل المفضلة، المقيمة، أو التي تم التفاعل مع ملفاتها
    interacted_resource_ids = set(user_liked_resources_ids)
    interacted_resource_ids.update(
        UserFileInteraction.objects.filter(user=user).values_list('resource_id', flat=True)
    )

    # إذا لم يكن لدى المستخدم أي تفاعلات، أظهر أحدث الموارد النشطة
    if not user_liked_resources_ids:
        return EducationalResource.objects.filter(is_active=True).exclude(id__in=list(interacted_resource_ids)).order_by('-created_at')[:limit]

    # جلب كائنات الموارد التي أعجب بها المستخدم
    user_liked_resources = EducationalResource.objects.filter(id__in=list(user_liked_resources_ids))

    # --- Phase 1: Content-Based Filtering ---
    # استخلاص الكلمات الرئيسية من تفضيلات المستخدم
    user_keywords = set()
    for resource in user_liked_resources:
        cleaned_title = clean_text(resource.title)
        cleaned_description = clean_text(resource.description)
        user_keywords.update(word for word in cleaned_title.split() if word and word not in ARABIC_STOP_WORDS)
        user_keywords.update(word for word in cleaned_description.split() if word and word not in ARABIC_STOP_WORDS)
    
    # تهيئة قاموس لتخزين درجات الموارد المرشحة
    # المفتاح: resource_id, القيمة: (score, resource_object)
    recommended_scores = {}

    # البحث عن موارد بناءً على الكلمات الرئيسية (Content-Based)
    if user_keywords:
        # ابحث عن موارد أخرى نشطة لم يتفاعل معها المستخدم بعد
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
            
            if match_score > 0: # فقط إذا كان هناك تطابق في الكلمات
                # وزن متوسط التقييم العام للمورد
                rating_score = (resource.avg_rating or 0) * 0.5
                total_score = match_score * 2 + rating_score # وزن أعلى للمطابقة النصية
                
                if resource.id not in recommended_scores or total_score > recommended_scores[resource.id][0]:
                    recommended_scores[resource.id] = (total_score, resource)

    # --- Phase 2: User-Similarity Inspired Filtering ---
    # الفكرة: ابحث عن مستخدمين آخرين لديهم موارد مفضلة/مقيمة عالياً مشتركة مع المستخدم الحالي.
    # ثم اقترح الموارد التي أعجبتهم ولم يتفاعل معها المستخدم الحالي.
    
    # ابحث عن المستخدمين الذين فضلوا أو قيموا نفس الموارد التي فضلها المستخدم الحالي
    # (على الأقل مورد واحد مشترك)
    similar_users_ids = UserFavoriteResource.objects.filter(
        resource__id__in=list(user_liked_resources_ids)
    ).exclude(
        user=user
    ).values_list('user_id', flat=True).distinct()

    similar_users_ids_from_ratings = EducationalResourceRating.objects.filter(
        resource__id__in=list(user_liked_resources_ids),
        rating__gte=4 # نعتبر التقييمات العالية فقط
    ).exclude(
        user=user
    ).values_list('user_id', flat=True).distinct()

    all_similar_users_ids = list(set(list(similar_users_ids) + list(similar_users_ids_from_ratings)))

    if all_similar_users_ids:
        # جلب الموارد التي فضلها هؤلاء المستخدمون المشابهون أو قيموها عالياً
        resources_from_similar_users = EducationalResource.objects.filter(is_active=True).filter(
            Q(favorited_by__user__id__in=all_similar_users_ids) |
            Q(ratings__user__id__in=all_similar_users_ids, ratings__rating__gte=4)
        ).exclude(
            id__in=list(interacted_resource_ids)
        ).annotate(
            avg_rating=Avg('ratings__rating'),
            num_ratings=Count('ratings')
        ).distinct() # للتأكد من عدم تكرار الموارد

        for resource in resources_from_similar_users:
            # يمكن إعطاء وزن أقل لهذه التوصيات مقارنة بالمحتوى المباشر
            score = (resource.avg_rating or 0) * 0.75 # وزن أقل
            if resource.id not in recommended_scores or score > recommended_scores[resource.id][0]:
                recommended_scores[resource.id] = (score, resource)

    # --- Phase 3: Item-Similarity Inspired Filtering ---
    # الفكرة: إذا أعجب المستخدم بالموارد X و Y، فابحث عن الموارد التي غالباً ما تظهر مع X و Y في تفضيلات المستخدمين الآخرين.

    # جمع جميع التفاعلات (المفضلة والتقييمات العالية) من جميع المستخدمين
    all_favorites = UserFavoriteResource.objects.all().values('user_id', 'resource_id')
    all_high_ratings = EducationalResourceRating.objects.filter(rating__gte=4).values('user_id', 'resource_id')

    user_resource_map = defaultdict(set)
    for entry in all_favorites:
        user_resource_map[entry['user_id']].add(entry['resource_id'])
    for entry in all_high_ratings:
        user_resource_map[entry['user_id']].add(entry['resource_id'])

    # بناء مصفوفة تشابه العناصر (بشكل مبسط)
    # item_pair_counts[(item1, item2)] = عدد المستخدمين الذين تفاعلوا مع كليهما
    item_pair_counts = defaultdict(int)
    for user_id, resources_set in user_resource_map.items():
        resources_list = sorted(list(resources_set)) # لضمان الترتيب المتسق للأزواج
        for i in range(len(resources_list)):
            for j in range(i + 1, len(resources_list)):
                item1, item2 = resources_list[i], resources_list[j]
                item_pair_counts[(item1, item2)] += 1
                item_pair_counts[(item2, item1)] += 1 # الترتيب لا يهم

    # اقتراح موارد بناءً على تشابه العناصر
    for liked_resource_id in user_liked_resources_ids:
        for (item1, item2), count in item_pair_counts.items():
            if item1 == liked_resource_id and item2 not in interacted_resource_ids:
                # كلما زاد عدد المستخدمين الذين فضلوا كلا الموردين، زادت درجة التوصية
                # يمكن استخدام مقاييس تشابه أكثر تعقيداً هنا (مثل Jaccard, Cosine)
                score = count * 0.1 # وزن منخفض نسبياً
                
                # جلب كائن المورد إذا لم يكن موجوداً بالفعل
                if item2 not in recommended_scores:
                    try:
                        resource = EducationalResource.objects.get(id=item2, is_active=True)
                        resource.avg_rating = resource.average_rating # تحميل الخصائص
                        resource.num_ratings = resource.total_ratings
                        recommended_scores[item2] = (score, resource)
                    except EducationalResource.DoesNotExist:
                        continue # تخطي الموارد غير الموجودة أو غير النشطة
                else:
                    # تحديث النتيجة إذا كانت النتيجة الجديدة أعلى
                    current_score, current_resource = recommended_scores[item2]
                    if score > current_score:
                        recommended_scores[item2] = (score, current_resource)


    # 4. تجميع وفرز الموارد الموصى بها
    final_recommendations_list = sorted(
        recommended_scores.values(),
        key=lambda x: x[0], # الفرز حسب درجة المطابقة
        reverse=True
    )

    # إرجاع أفضل N مورد
    # تأكد من إرجاع كائنات الموارد فقط
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
            from news.models import NewsItem
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
        
        # إضافة الموارد الموصى بها
        context['recommended_resources'] = get_recommended_resources_for_user(self.request.user, limit=4) # عرض 4 موارد
        
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
        context['tasks_completion_labels_raw'] = [d.strftime('%Y-%m-%d') for d in days_range_raw]
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


class EducationalResourcesView(GenericListView):
    """
    عرض قائمة بالموارد التعليمية مع دعم التقييمات والمفضلة.
    """
    model = EducationalResource
    template_name = 'core/educational_resources.html'
    context_object_name = 'resources'
    paginate_by = 10
    
    def get_queryset(self):
        # جلب الموارد النشطة فقط، مع إضافة متوسط التقييم وعدد التقييمات
        queryset = EducationalResource.objects.filter(is_active=True).annotate(
            avg_rating=Avg('ratings__rating'),
            num_ratings=Count('ratings')
        ).order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # جلب تقييم المستخدم الحالي لكل مورد
            user_ratings = EducationalResourceRating.objects.filter(user=self.request.user)
            context['user_ratings_map'] = {rating.resource_id: rating for rating in user_ratings}
            
            # جلب الموارد المفضلة للمستخدم الحالي
            favorite_resources = UserFavoriteResource.objects.filter(user=self.request.user).values_list('resource_id', flat=True)
            context['user_favorite_resources'] = list(favorite_resources)

            # نموذج التقييم الجديد (يمكن استخدامه في مودال أو جزء مخفي)
            context['rating_form'] = EducationalResourceRatingForm()
        return context

    def post(self, request, *args, **kwargs):
        # معالجة إرسال التقييم
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

            # حاول تحديث التقييم الموجود أو إنشاء تقييم جديد
            rating_obj, created = EducationalResourceRating.objects.update_or_create(
                resource=resource,
                user=request.user,
                defaults={'rating': rating_value, 'review_text': review_text}
            )
            
            if created:
                messages.success(request, "تم إضافة تقييمك بنجاح!")
            else:
                messages.success(request, "تم تحديث تقييمك بنجاح!")
            
            # يمكنك إعادة التوجيه أو إرجاع JsonResponse لـ AJAX
            return redirect('core:educational_resources') # أو JsonResponse({'status': 'success', 'message': 'Rating saved'})
        else:
            messages.error(request, "حدث خطأ في التقييم. يرجى التحقق من البيانات.")
            # إذا كان النموذج غير صالح، أعد عرض الصفحة مع الأخطاء
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            context['rating_form'] = form # أعد النموذج مع الأخطاء
            return render(request, self.template_name, context)


@login_required
@require_POST
def toggle_favorite_resource(request):
    """
    تبديل حالة المفضلة لمورد تعليمي عبر AJAX.
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
        # إذا كان موجوداً بالفعل، احذفه (إزالة من المفضلة)
        favorite.delete()
        return JsonResponse({'status': 'removed', 'message': 'تمت إزالة المورد من المفضلة.'})
    else:
        # إذا تم إنشاؤه للتو، فهذا يعني أنه أضيف للمفضلة
        return JsonResponse({'status': 'added', 'message': 'تمت إضافة المورد إلى المفضلة.'})


class UserFavoriteResourcesListView(LoginRequiredMixin, GenericListView):
    """
    عرض قائمة بالموارد التعليمية المفضلة للمستخدم الحالي.
    """
    model = UserFavoriteResource
    template_name = 'core/favorite_resources.html'
    context_object_name = 'favorite_entries'
    paginate_by = 10

    def get_queryset(self):
        # جلب الموارد المفضلة للمستخدم الحالي فقط
        # select_related('resource') لتحميل بيانات المورد لتجنب استعلامات إضافية
        return UserFavoriteResource.objects.filter(user=self.request.user).select_related('resource').order_by('-added_at')


# --- دوال عرض جديدة للأدوات والمرافق (من التحديث السابق) ---

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

