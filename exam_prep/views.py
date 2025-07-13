from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q # لاستخدام Count و Q في الاستعلامات
from django.urls import reverse_lazy # لاستخدام reverse_lazy في التحويلات
from django.utils import timezone # لاستخدام التوقيت في الحقول الزمنية
from django.forms import ModelForm # لاستخدام ModelForm لإنشاء نموذج تعديل
from django.shortcuts import get_object_or_404, redirect # لاستخدام get_object_or_404 و redirect
from django.utils.translation import gettext_lazy as _

from .models import ExamPrayer, ExamTip, Report, UserActivity # استيراد النماذج الجديدة

# --- Mixins for Admin Views ---
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin يضمن أن المستخدم مسجل الدخول وموظف (staff).
    """
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        # يمكنك توجيه المستخدم إلى صفحة معينة أو عرض رسالة خطأ
        return redirect(reverse_lazy('exam_prep:exam_resources')) # مثال: توجيه إلى صفحة الموارد العادية


# --- Existing View ---
class ExamResourcesView(LoginRequiredMixin, TemplateView):
    template_name = 'exam_prep/exam_resources.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # جلب الأدعية النشطة فقط، مرتبة
        context['prayers'] = ExamPrayer.objects.filter(is_active=True).order_by('order', 'id')

        # جلب النصائح النشطة فقط، مقسمة ومرتبة
        active_tips = ExamTip.objects.filter(is_active=True).order_by('order', 'id')
        
        context['tips_general'] = active_tips.filter(category='general')
        context['tips_before'] = active_tips.filter(category='before')
        context['tips_during'] = active_tips.filter(category='during')
        context['tips_after'] = active_tips.filter(category='after')
        
        return context


# --- New Admin Views ---

class AdminDashboardView(StaffRequiredMixin, TemplateView):
    """
    لوحة تحكم المشرفين تعرض إحصائيات عامة وروابط سريعة.
    """
    template_name = 'exam_prep/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات الإبلاغات
        context['total_reports'] = Report.objects.count()
        context['pending_reports'] = Report.objects.filter(status='pending').count()
        context['reviewed_reports'] = Report.objects.filter(status='reviewed').count()
        context['resolved_reports'] = Report.objects.filter(status='resolved').count()
        
        # إحصائيات أنشطة المستخدمين (أمثلة)
        context['total_activities'] = UserActivity.objects.count()
        # يمكنك إضافة المزيد من الإحصائيات هنا، مثل:
        # context['unique_users_today'] = UserActivity.objects.filter(timestamp__date=timezone.now().date()).values('user').distinct().count()
        # context['top_activity_types'] = UserActivity.objects.values('activity_type').annotate(count=Count('activity_type')).order_by('-count')[:5]

        # إحصائيات المحتوى
        context['total_prayers'] = ExamPrayer.objects.count()
        context['active_prayers'] = ExamPrayer.objects.filter(is_active=True).count()
        context['total_tips'] = ExamTip.objects.count()
        context['active_tips'] = ExamTip.objects.filter(is_active=True).count()

        return context


class ReportListView(StaffRequiredMixin, ListView):
    """
    يعرض قائمة بجميع الإبلاغات، مع إمكانية التصفية.
    """
    model = Report
    template_name = 'exam_prep/report_list.html'
    context_object_name = 'reports'
    paginate_by = 10 # تقسيم النتائج على صفحات

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related('reporter', 'reviewed_by', 'content_type') # تحسين الأداء


class ReportUpdateForm(ModelForm):
    """
    نموذج لتعديل حالة الإبلاغ وملاحظات المشرف.
    """
    class Meta:
        model = Report
        fields = ['status', 'admin_notes']


class ReportDetailView(StaffRequiredMixin, UpdateView):
    """
    يعرض تفاصيل إبلاغ معين ويسمح للمشرف بتغيير حالته وإضافة ملاحظات.
    """
    model = Report
    template_name = 'exam_prep/report_detail.html'
    context_object_name = 'report'
    form_class = ReportUpdateForm # استخدام النموذج المخصص للتعديل
    
    def get_success_url(self):
        return reverse_lazy('exam_prep:report_list') # العودة إلى قائمة الإبلاغات بعد التعديل

    def form_valid(self, form):
        # تحديث حقول المراجعة عند تغيير الحالة
        if form.instance.status != 'pending' and not form.instance.reviewed_by:
            form.instance.reviewed_by = self.request.user
            form.instance.reviewed_at = timezone.now()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # يمكنك إضافة أي بيانات إضافية هنا إذا أردت
        return context


class UserActivityListView(StaffRequiredMixin, ListView):
    """
    يعرض قائمة بأنشطة المستخدمين، مع إمكانية التصفية.
    """
    model = UserActivity
    template_name = 'exam_prep/user_activity_list.html'
    context_object_name = 'activities'
    paginate_by = 20 # تقسيم النتائج على صفحات

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.GET.get('user_id')
        activity_type = self.request.GET.get('activity_type')

        if user_id:
            queryset = queryset.filter(user__id=user_id)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        return queryset.select_related('user', 'content_type') # تحسين الأداء

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # تمرير قائمة بأنواع الأنشطة الفريدة للمساعدة في التصفية
        context['activity_types'] = UserActivity.objects.values_list('activity_type', flat=True).distinct().order_by('activity_type')
        return context

