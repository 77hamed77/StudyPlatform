from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView # إضافة CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin # إضافة PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import NewsItem, NewsCategory
from .forms import NewsItemForm # افتراض وجود النموذج إذا كنت ستستخدمه
# from .filters import NewsFilter # إذا كنت ستستخدم django-filter

class NewsListView(ListView):
    model = NewsItem
    template_name = 'news/news_list.html'
    context_object_name = 'news_list' # اسم أوضح للـ context
    paginate_by = 9 # عدد الأخبار في كل صفحة

    def get_queryset(self):
        queryset = NewsItem.objects.filter(is_published=True).select_related('category', 'author')
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(NewsCategory, slug=category_slug)
            queryset = queryset.filter(category=category)
            self.category = category # لتمريره للـ context
        else:
            self.category = None

        # إزالة الأخبار المثبتة من القائمة الرئيسية إذا كانت ستُعرض بشكل منفصل
        queryset = queryset.filter(is_important=False).order_by('-publication_date')
        
        # مثال لتطبيق فلتر (إذا كنت تستخدمه)
        # self.filterset = NewsFilter(self.request.GET, queryset=queryset)
        # return self.filterset.qs
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['filter_form'] = self.filterset.form if hasattr(self, 'filterset') else None
        context['current_category'] = getattr(self, 'category', None)
        
        # جلب الأخبار المثبتة بشكل منفصل
        context['pinned_news'] = NewsItem.objects.filter(
            is_published=True,
            is_important=True
        ).select_related('category', 'author').order_by('-publication_date')[:3] # عرض أحدث 3 أخبار مثبتة
        
        context['all_categories'] = NewsCategory.objects.all().order_by('name') # لعرض قائمة بالتصنيفات للفلترة
        return context


class NewsDetailView(DetailView):
    model = NewsItem
    template_name = 'news/news_detail.html'
    context_object_name = 'news_item' # اسم أوضح

    def get_queryset(self):
        # عرض تفاصيل الخبر فقط إذا كان منشورًا (أو إذا كان المستخدم مشرفًا)
        qs = super().get_queryset().filter(is_published=True).select_related('category', 'author')
        # إذا أردت السماح للمشرفين برؤية الأخبار غير المنشورة:
        # if self.request.user.is_staff:
        #     qs = super().get_queryset().select_related('category', 'author')
        return qs

    def get_object(self, queryset=None):
        # استخدام slug وتاريخ النشر لجلب الكائن
        # هذا يتطلب تعديل المسار في urls.py
        if queryset is None:
            queryset = self.get_queryset()
        
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        slug = self.kwargs.get('slug')

        if not all([year, month, day, slug]):
            raise AttributeError(
                f"Generic detail view {self.__class__.__name__} must be called with "
                f"either an object pk or a slug and date."
            )
        
        # تحويل إلى أرقام صحيحة
        try:
            year = int(year)
            month = int(month)
            day = int(day)
        except ValueError:
            raise Http404(_("Invalid date format in URL."))

        return get_object_or_404(
            queryset,
            publication_date__year=year,
            publication_date__month=month,
            publication_date__day=day,
            slug=slug
        )

# Views لإنشاء وتعديل وحذف الأخبار (تتطلب صلاحيات)
class NewsCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = NewsItem
    form_class = NewsItemForm # استخدم النموذج الذي أنشأناه
    template_name = 'news/news_form.html' # ستحتاج لإنشاء هذا القالب
    permission_required = 'news.add_newsitem' # الصلاحية المطلوبة
    # success_url = reverse_lazy('news:news_list') # سيتم استخدام get_absolute_url من الموديل

    def form_valid(self, form):
        form.instance.author = self.request.user # تعيين المستخدم الحالي كمؤلف
        messages.success(self.request, _("تم إنشاء الخبر بنجاح!"))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs): # لإضافة عنوان للصفحة
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("إضافة خبر جديد")
        return context


class NewsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = NewsItem
    form_class = NewsItemForm
    template_name = 'news/news_form.html'
    permission_required = 'news.change_newsitem'
    context_object_name = 'news_item' # ليكون الاسم متسقًا في القالب

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث الخبر بنجاح!"))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _(f"تعديل الخبر: {self.object.title}")
        return context


class NewsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = NewsItem
    template_name = 'news/news_confirm_delete.html' # ستحتاج لإنشاء هذا القالب
    success_url = reverse_lazy('news:news_list')
    permission_required = 'news.delete_newsitem'
    context_object_name = 'news_item'

    def form_valid(self, form):
        news_title = self.object.title
        messages.success(self.request, _(f"تم حذف الخبر '{news_title}' بنجاح."))
        return super().form_valid(form)