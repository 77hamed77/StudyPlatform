from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ExamPrayer, ExamTip
from django.utils.translation import gettext_lazy as _ # غير مستخدم مباشرة هنا ولكن جيد إبقاؤه

class ExamResourcesView(LoginRequiredMixin, TemplateView): # تم تغيير الاسم ليكون أكثر عمومية
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
        
        # يمكنك إضافة أي بيانات أخرى للـ context هنا إذا أردت
        # context['page_title'] = _("ركن الاستعداد للامتحانات") # إذا أردت تمرير عنوان للصفحة
        return context