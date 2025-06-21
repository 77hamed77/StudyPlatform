from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .models import Task # تأكد من أن موديل Subject مُستورد إذا كنت ستستخدمه في TaskFilter
from .forms import TaskForm
from .filters import TaskFilter # استيراد الفلتر إذا كنت قد أنشأته

class TaskOwnerRequiredMixin(UserPassesTestMixin):
    """
    Mixin للتأكد من أن المستخدم الحالي هو مالك المهمة.
    يُستخدم مع Views التي تتعامل مع كائن مهمة واحد (Detail, Update, Delete).
    """
    raise_exception = False # إذا كان True سيرفع PermissionDenied، وإلا سيقوم بإعادة التوجيه

    def test_func(self):
        task = self.get_object()
        return self.request.user == task.user

    def handle_no_permission(self):
        messages.error(self.request, _("ليس لديك صلاحية للوصول إلى هذه المهمة أو تعديلها."))
        # يمكنك توجيه المستخدم إلى قائمة مهامه أو أي صفحة أخرى مناسبة
        return redirect('tasks:task_list')


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks' # اسم الـ context ليكون واضحًا في القالب
    paginate_by = 9 # عدد المهام في كل صفحة (يتناسب مع تصميم 3 كروت في الصف)

    def get_queryset(self):
        # 1. جلب مهام المستخدم الحالي فقط
        queryset = Task.objects.filter(user=self.request.user).select_related('subject').order_by('status', 'due_date', 'created_at')
        
        # 2. تطبيق الفلترة باستخدام TaskFilter
        # يجب أن يكون self.filterset مُعرفًا ليتمكن get_context_data من الوصول إليه
        self.filterset = TaskFilter(self.request.GET, queryset=queryset, request=self.request) # تمرير request للفلتر
        
        # إرجاع الـ queryset المُفلتر
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # تمرير نموذج الفلتر للقالب
        context['filter_form'] = self.filterset.form
        
        # إضافة إحصائيات للمستخدم الحالي (اختياري)
        user_tasks = Task.objects.filter(user=self.request.user)
        context['pending_tasks_count'] = user_tasks.filter(status='pending').count()
        context['inprogress_tasks_count'] = user_tasks.filter(status='in_progress').count()
        context['completed_tasks_count'] = user_tasks.filter(status='completed').count()
        context['total_tasks_count'] = user_tasks.count()
        return context


class TaskDetailView(LoginRequiredMixin, TaskOwnerRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task' # اسم الـ context للكائن

    def get_queryset(self):
        # تأكد من جلب المهام الخاصة بالمستخدم فقط إذا لم يتم استخدام TaskOwnerRequiredMixin بشكل كامل
        # لكن TaskOwnerRequiredMixin يجب أن يعتني بهذا.
        # إضافة select_related لتحسين الأداء إذا كان هناك حقول ForeignKey أخرى.
        return super().get_queryset().filter(user=self.request.user).select_related('subject')


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    # لا حاجة لـ success_url هنا، سيتم استخدام get_success_url من الموديل إذا وُجد، أو يمكننا تحديده هنا

    def get_form_kwargs(self):
        """
        تمرير المستخدم الحالي للنموذج، حتى يتمكن النموذج من استخدامه
        (مثلاً لفلترة خيارات ForeignKey إذا لزم الأمر).
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user # تعيين المستخدم الحالي كمالك للمهمة
        messages.success(self.request, _("تم إنشاء المهمة بنجاح!"))
        return super().form_valid(form)

    def get_success_url(self):
        # التوجيه لصفحة تفاصيل المهمة التي تم إنشاؤها للتو
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs): # لإضافة عنوان للصفحة
        context = super().get_context_data(**kwargs)
        context['page_title'] = _("إنشاء مهمة جديدة")
        return context


class TaskUpdateView(LoginRequiredMixin, TaskOwnerRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    context_object_name = 'task' # ليكون الاسم متسقًا في القالب

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # قد لا يكون ضروريًا دائمًا للتحديث، لكنه لا يضر
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث المهمة بنجاح!"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _(f"تعديل المهمة: {self.object.title}")
        return context


class TaskDeleteView(LoginRequiredMixin, TaskOwnerRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html' # قالب تأكيد الحذف
    success_url = reverse_lazy('tasks:task_list') # بعد الحذف، العودة لقائمة المهام
    context_object_name = 'task' # استخدام task بدلاً من object ليكون أوضح في القالب

    def form_valid(self, form):
        task_title = self.object.title
        response = super().form_valid(form) # الحذف يتم هنا
        messages.success(self.request, _(f"تم حذف المهمة '{task_title}' بنجاح."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _(f"تأكيد حذف المهمة: {self.object.title}")
        return context


# --- Views لتغيير حالة المهمة ---
@login_required
@require_POST # لضمان أن هذه الـ views تُستدعى فقط عبر POST requests
def mark_task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user) # التأكد أن المستخدم يملك المهمة
    if task.status != 'completed':
        task.status = 'completed'
        task.save(update_fields=['status', 'updated_at']) # تحديد الحقول المحدثة لتحسين الأداء
        messages.success(request, _(f"تم تمييز المهمة '{task.title}' كمكتملة."))
    else:
        messages.info(request, _(f"المهمة '{task.title}' مكتملة بالفعل."))
    return redirect(task.get_absolute_url()) # استخدام get_absolute_url للعودة لصفحة التفاصيل

@login_required
@require_POST
def mark_task_inprogress(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == 'pending':
        task.status = 'in_progress'
        task.save(update_fields=['status', 'updated_at'])
        messages.info(request, _(f"بدأت العمل على المهمة '{task.title}'."))
    elif task.status == 'in_progress':
        messages.info(request, _(f"المهمة '{task.title}' قيد التنفيذ بالفعل."))
    else:
        messages.warning(request, _(f"لا يمكن بدء العمل على المهمة '{task.title}' وهي بحالة '{task.get_status_display()}'."))
    return redirect(task.get_absolute_url())

# يمكنك إضافة views مشابهة للحالات الأخرى (pending, postponed) إذا أردت أزرارًا مخصصة لها
# مثال:
# @login_required
# @require_POST
# def mark_task_pending(request, pk):
#     task = get_object_or_404(Task, pk=pk, user=request.user)
#     if task.status != 'pending':
#         task.status = 'pending'
#         task.save(update_fields=['status', 'updated_at'])
#         messages.info(request, _(f"تم تغيير حالة المهمة '{task.title}' إلى قيد الانتظار."))
#     return redirect(task.get_absolute_url())