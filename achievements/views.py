from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin # أو اجعلها صفحة عامة
from .models import Badge
from django.utils.translation import gettext_lazy as _

class AllBadgesListView(LoginRequiredMixin, ListView): # أو بدون LoginRequiredMixin
    model = Badge
    template_name = 'achievements/all_badges_list.html' # ستحتاج لإنشاء هذا القالب
    context_object_name = 'all_badges'
    paginate_by = 12 # مثال
    ordering = ['order', 'name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("جميع الشارات المتاحة")
        # يمكنك إضافة أي بيانات أخرى هنا
        return context