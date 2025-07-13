from django.contrib.auth.decorators import login_required # <--- أضف هذا السطر
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q # For complex lookups if needed
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST, require_GET

from .models import StudyGroup, GroupMembership, GroupMessage
from .forms import StudyGroupForm, GroupMessageForm

# --- Study Group Views ---

class StudyGroupListView(LoginRequiredMixin, ListView):
    """
    يعرض قائمة بجميع المجموعات الدراسية المتاحة.
    """
    model = StudyGroup
    template_name = 'community/study_group_list.html'
    context_object_name = 'study_groups'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        # Optional: Filter groups based on search query or user's subjects
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(subject__name__icontains=search_query)
            )
        
        # Annotate queryset with whether the current user is a member
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_member=models.Exists(
                    GroupMembership.objects.filter(group=models.OuterRef('pk'), user=self.request.user)
                )
            )
        return queryset.select_related('subject', 'creator')


class StudyGroupCreateView(LoginRequiredMixin, CreateView):
    """
    يسمح للمستخدمين بإنشاء مجموعة دراسية جديدة.
    """
    model = StudyGroup
    form_class = StudyGroupForm
    template_name = 'community/study_group_create.html'
    success_url = reverse_lazy('community:study_group_list') # Redirect to group list after creation

    def form_valid(self, form):
        form.instance.creator = self.request.user # Set the creator to the current user
        response = super().form_valid(form)
        
        # Automatically make the creator an admin of the group
        GroupMembership.objects.create(
            group=self.object,
            user=self.request.user,
            role='admin'
        )
        messages.success(self.request, "تم إنشاء المجموعة الدراسية بنجاح!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form() # Ensure form is passed to context
        return context


class StudyGroupDetailView(LoginRequiredMixin, DetailView):
    """
    يعرض تفاصيل مجموعة دراسية محددة، بما في ذلك الأعضاء والرسائل.
    """
    model = StudyGroup
    template_name = 'community/study_group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        user = self.request.user

        # Check if user is a member of this group
        is_member = GroupMembership.objects.filter(group=group, user=user).exists()
        context['is_member'] = is_member

        if is_member:
            context['members'] = group.memberships.select_related('user').order_by('role', 'user__username')
            context['messages'] = group.messages.select_related('sender').order_by('timestamp')
            context['message_form'] = GroupMessageForm()
        else:
            context['members'] = None
            context['messages'] = None
            context['message_form'] = None
            messages.info(self.request, "يجب أن تكون عضواً في هذه المجموعة لعرض محتواها.")

        return context

# --- AJAX Endpoints for Group Actions ---

@login_required
@require_POST
def join_leave_group(request, pk):
    """
    نقطة نهاية AJAX للانضمام إلى مجموعة أو مغادرتها.
    """
    group = get_object_or_404(StudyGroup, pk=pk)
    user = request.user

    membership = GroupMembership.objects.filter(group=group, user=user).first()

    if membership:
        # User is already a member, so leave the group
        membership.delete()
        status = 'left'
        message = f"لقد غادرت مجموعة '{group.name}'."
    else:
        # User is not a member, so join the group
        GroupMembership.objects.create(group=group, user=user, role='member')
        status = 'joined'
        message = f"لقد انضممت إلى مجموعة '{group.name}' بنجاح!"
    
    return JsonResponse({'status': status, 'message': message})


@login_required
@require_POST
def send_group_message(request, pk):
    """
    نقطة نهاية AJAX لإرسال رسالة في مجموعة دراسية.
    """
    group = get_object_or_404(StudyGroup, pk=pk)
    user = request.user

    # Check if the user is a member of the group
    if not GroupMembership.objects.filter(group=group, user=user).exists():
        return JsonResponse({'status': 'error', 'message': 'يجب أن تكون عضواً في هذه المجموعة لإرسال الرسائل.'}, status=403)

    form = GroupMessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.group = group
        message.sender = user
        message.save()
        
        # Return the new message data for immediate display
        return JsonResponse({
            'status': 'success',
            'message': 'تم إرسال الرسالة بنجاح!',
            'data': {
                'sender': user.username,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'), # Format timestamp
            }
        })
    else:
        return JsonResponse({'status': 'error', 'message': 'الرسالة فارغة أو غير صالحة.'}, status=400)


@login_required
@require_GET
def get_group_messages(request, pk):
    """
    نقطة نهاية AJAX لجلب رسائل جديدة لمجموعة دراسية.
    يمكن استخدامها لتحديث الدردشة بشكل دوري.
    """
    group = get_object_or_404(StudyGroup, pk=pk)
    user = request.user

    # Check if the user is a member of the group
    if not GroupMembership.objects.filter(group=group, user=user).exists():
        return JsonResponse({'status': 'error', 'message': 'يجب أن تكون عضواً في هذه المجموعة لعرض الرسائل.'}, status=403)

    # Get messages, optionally after a certain timestamp for new messages
    last_message_timestamp_str = request.GET.get('last_timestamp')
    messages_queryset = group.messages.select_related('sender')

    if last_message_timestamp_str:
        try:
            # Parse timestamp from client (e.g., '2023-10-26 10:30:00')
            last_message_timestamp = timezone.datetime.strptime(last_message_timestamp_str, '%Y-%m-%d %H:%M:%S')
            # Ensure timezone-aware comparison
            if timezone.is_naive(last_message_timestamp):
                last_message_timestamp = timezone.make_aware(last_message_timestamp, timezone.get_current_timezone())
            messages_queryset = messages_queryset.filter(timestamp__gt=last_message_timestamp)
        except ValueError:
            pass # Ignore invalid timestamp, return all messages

    messages_data = []
    for message in messages_queryset.order_by('timestamp'):
        messages_data.append({
            'sender': message.sender.username,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_current_user': message.sender == user # To style messages differently for current user
        })
    
    return JsonResponse({'status': 'success', 'messages': messages_data})

