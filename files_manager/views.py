from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import models

from .models import MainFile, StudentSummary, UserFileInteraction, Subject, FileType
from .forms import StudentSummaryUploadForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# --- Main Files List ---
class MainFileListView(LoginRequiredMixin, ListView):
    model = MainFile
    template_name = 'files_manager/main_file_list.html'
    context_object_name = 'files'
    paginate_by = 9

    def get_queryset(self):
        queryset = MainFile.objects.select_related(
            'subject', 'lecturer', 'file_type', 'uploaded_by'
        ).order_by('-uploaded_at')
        subject_id = self.request.GET.get('subject')
        file_type_id = self.request.GET.get('type')
        query = self.request.GET.get('q')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if file_type_id:
            queryset = queryset.filter(file_type_id=file_type_id)
        if query:
            queryset = queryset.filter(
                models.Q(title__icontains=query) | models.Q(description__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        files_on_page = context.get(self.context_object_name, [])
        if self.request.user.is_authenticated and files_on_page:
            user_interactions = UserFileInteraction.objects.filter(
                user=self.request.user,
                main_file_id__in=[f.id for f in files_on_page]
            ).values('main_file_id', 'marked_as_read')
            interactions_map = {item['main_file_id']: item for item in user_interactions}
            for file_obj in files_on_page:
                interaction_data = interactions_map.get(file_obj.id)
                file_obj.current_user_marked_as_read = interaction_data['marked_as_read'] if interaction_data else False
        else:
            for file_obj in files_on_page:
                file_obj.current_user_marked_as_read = False

        context['subjects_for_filter'] = Subject.objects.all().order_by('name')
        context['file_types_for_filter'] = FileType.objects.all().order_by('name')
        return context

# --- Main File Detail ---
class MainFileDetailView(LoginRequiredMixin, DetailView):
    model = MainFile
    template_name = 'files_manager/main_file_detail.html'
    context_object_name = 'file_obj'

    def get_queryset(self):
        return super().get_queryset().select_related('subject', 'lecturer', 'file_type', 'uploaded_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            interaction, _ = UserFileInteraction.objects.get_or_create(
                user=self.request.user,
                main_file=self.object
            )
            context['current_user_marked_as_read'] = interaction.marked_as_read
        else:
            context['current_user_marked_as_read'] = False
        return context

# --- Student Summary Upload ---
class StudentSummaryUploadView(LoginRequiredMixin, CreateView):
    model = StudentSummary
    form_class = StudentSummaryUploadForm
    template_name = 'files_manager/student_summary_upload.html'
    success_url = reverse_lazy('files_manager:my_summaries_list')

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, _("تم رفع ملخصك بنجاح. سيتم مراجعته من قبل المشرف قريباً."))
        return super().form_valid(form)

# --- Public Student Summaries List ---
class StudentSummaryListView(LoginRequiredMixin, ListView):
    model = StudentSummary
    template_name = 'files_manager/student_summary_list.html'
    context_object_name = 'summaries'
    paginate_by = 9

    def get_queryset(self):
        return StudentSummary.objects.filter(
            status='approved'
        ).select_related('subject', 'uploaded_by').order_by('-uploaded_at')

# --- My Student Summaries List ---
class MyStudentSummariesListView(LoginRequiredMixin, ListView):
    model = StudentSummary
    template_name = 'files_manager/my_student_summaries_list.html'
    context_object_name = 'my_summaries'
    paginate_by = 10

    def get_queryset(self):
        return StudentSummary.objects.filter(
            uploaded_by=self.request.user
        ).select_related('subject').order_by('-uploaded_at')

# --- Toggle Marked as Read/Unread (AJAX) ---
@login_required
@require_POST
def toggle_file_read_status(request):
    file_id = request.POST.get('file_id')
    if not file_id:
        return JsonResponse({'status': 'error', 'message': _('File ID is missing.')}, status=400)
    try:
        main_file = MainFile.objects.get(pk=file_id)
    except MainFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': _('File not found.')}, status=404)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': _('Invalid File ID.')}, status=400)

    interaction, _ = UserFileInteraction.objects.get_or_create(
        user=request.user,
        main_file=main_file
    )
    interaction.marked_as_read = not interaction.marked_as_read
    if interaction.marked_as_read:
        interaction.marked_at = timezone.now()
    else:
        interaction.marked_at = None
    interaction.save(update_fields=['marked_as_read', 'marked_at'])

    return JsonResponse({
        'status': 'success',
        'marked_as_read': interaction.marked_as_read,
        'file_id': main_file.pk
    })