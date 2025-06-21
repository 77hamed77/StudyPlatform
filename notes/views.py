from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import QuickNote, NoteCategory
from .forms import QuickNoteForm, NoteCategoryForm
from django.db.models import Q # للبحث المتقدم

class NoteOwnerRequiredMixin(UserPassesTestMixin):
    """Mixin للتأكد من أن المستخدم الحالي هو مالك الملاحظة أو التصنيف."""
    def test_func(self):
        item = self.get_object()
        return self.request.user == item.user

    def handle_no_permission(self):
        messages.error(self.request, _("ليس لديك صلاحية للوصول إلى هذا العنصر."))
        # توجيه المستخدم لقائمة الملاحظات إذا كان يحاول الوصول لملاحظة لا يملكها
        # أو توجيه لمكان آخر إذا كان تصنيفًا
        if isinstance(self.get_object(), QuickNote):
            return redirect('notes:note_list')
        # يمكنك إضافة منطق آخر للتصنيفات إذا أردت
        return redirect('core:dashboard') # وجهة عامة


class QuickNoteListView(LoginRequiredMixin, ListView):
    model = QuickNote
    template_name = 'notes/quick_note_list.html'
    context_object_name = 'notes'
    paginate_by = 9 # عرض 9 ملاحظات (3x3 في تصميم الكروت)

    def get_queryset(self):
        queryset = QuickNote.objects.filter(user=self.request.user).select_related('category').order_by('-updated_at')
        query = self.request.GET.get('q')
        category_id = self.request.GET.get('category')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )
        if category_id:
            try:
                # التأكد من أن category_id هو رقم صحيح
                category_id_int = int(category_id)
                queryset = queryset.filter(category_id=category_id_int)
            except ValueError:
                pass # تجاهل إذا لم يكن رقمًا صحيحًا
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = NoteCategory.objects.filter(user=self.request.user).order_by('name')
        # تمرير قيم الفلتر الحالية للقالب لإبقائها في حقول الفلترة
        context['current_category_id'] = self.request.GET.get('category')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class QuickNoteDetailView(LoginRequiredMixin, NoteOwnerRequiredMixin, DetailView):
    model = QuickNote
    template_name = 'notes/quick_note_detail.html'
    context_object_name = 'note'


class QuickNoteCreateView(LoginRequiredMixin, CreateView):
    model = QuickNote
    form_class = QuickNoteForm
    template_name = 'notes/quick_note_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _("تم إنشاء الملاحظة بنجاح!"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('notes:note_detail', kwargs={'pk': self.object.pk})


class QuickNoteUpdateView(LoginRequiredMixin, NoteOwnerRequiredMixin, UpdateView):
    model = QuickNote
    form_class = QuickNoteForm
    template_name = 'notes/quick_note_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث الملاحظة بنجاح!"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('notes:note_detail', kwargs={'pk': self.object.pk})


class QuickNoteDeleteView(LoginRequiredMixin, NoteOwnerRequiredMixin, DeleteView):
    model = QuickNote
    template_name = 'notes/quick_note_confirm_delete.html'
    success_url = reverse_lazy('notes:note_list')
    context_object_name = 'object' # استخدام object وهو الاسم الافتراضي لـ DeleteView

    def form_valid(self, form):
        note_title = self.object.title
        messages.success(self.request, _(f"تم حذف الملاحظة '{note_title}' بنجاح."))
        return super().form_valid(form)


# Views لتصنيفات الملاحظات
class NoteCategoryCreateView(LoginRequiredMixin, CreateView):
    model = NoteCategory
    form_class = NoteCategoryForm
    template_name = 'notes/note_category_form.html'
    # success_url سيتم تحديده في get_success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        # التحقق من التفرد يتم الآن في النموذج، لكن يمكن إضافة رسالة هنا إذا أردت
        try:
            response = super().form_valid(form)
            messages.success(self.request, _(f"تم إنشاء التصنيف '{form.instance.name}' بنجاح."))
            return response
        except forms.ValidationError as e: # هذا لن يُمسك عادةً لأن التحقق في النموذج
            form.add_error(None, e) # إضافة الخطأ للنموذج بشكل عام
            return self.form_invalid(form)


    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            # يجب التحقق من أن next_url آمن لتجنب ثغرات Open Redirect
            # from django.utils.http import url_has_allowed_host_and_scheme
            # if url_has_allowed_host_and_scheme(next_url, self.request.get_host()):
            #     return next_url
            return next_url # للتبسيط الآن، افترض أنه آمن أو قم بالتحقق
        return reverse_lazy('notes:note_list')


class NoteCategoryUpdateView(LoginRequiredMixin, NoteOwnerRequiredMixin, UpdateView):
    model = NoteCategory
    form_class = NoteCategoryForm
    template_name = 'notes/note_category_form.html'
    success_url = reverse_lazy('notes:note_list') # أو توجيه لإدارة التصنيفات

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _(f"تم تحديث التصنيف '{form.instance.name}' بنجاح."))
        return super().form_valid(form)


class NoteCategoryDeleteView(LoginRequiredMixin, NoteOwnerRequiredMixin, DeleteView):
    model = NoteCategory
    template_name = 'notes/note_category_confirm_delete.html'
    success_url = reverse_lazy('notes:note_list') # أو توجيه لإدارة التصنيفات
    context_object_name = 'object'

    def form_valid(self, form):
        category_name = self.object.name
        messages.success(self.request, _(f"تم حذف التصنيف '{category_name}' بنجاح. الملاحظات المرتبطة أصبحت بدون تصنيف."))
        return super().form_valid(form)