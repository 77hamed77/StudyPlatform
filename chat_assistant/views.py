import requests
import os # For environment variables
import json
from django.shortcuts import render
from django.views.generic import ListView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_GET
from django.db import models # Import models for models.Q
from files_manager.models import MainFile # Assuming MainFile is in files_manager app
from core.models import AcademicProgress # Import AcademicProgress for study plan suggestions
from .models import ChatInteraction # Ensure ChatInteraction is imported from models.py

class ChatAssistantView(LoginRequiredMixin, ListView):
    template_name = 'chat_assistant/chat_assistant.html'
    context_object_name = 'files'

    def get_queryset(self):
        """
        Retrieves a list of lectures based on search and filter criteria.
        """
        queryset = MainFile.objects.select_related('subject', 'lecturer', 'file_type').order_by('-uploaded_at')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(models.Q(title__icontains=q) | models.Q(description__icontains=q))
        
        academic_year = self.request.GET.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        semester = self.request.GET.get('semester')
        if semester:
            queryset = queryset.filter(semester=semester)
        
        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds additional data to the context, such as academic years and semesters.
        """
        context = super().get_context_data(**kwargs)
        context['academic_years'] = MainFile.objects.values_list('academic_year', flat=True).distinct().order_by('academic_year')
        context['semesters'] = MainFile.SEMESTER_CHOICES
        return context

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests, including chat API requests.
        """
        question = request.GET.get('question')
        lecture_id = request.GET.get('lecture_id')
        action = request.GET.get('action', 'ask') # New: to differentiate AI actions

        if question and request.user.is_authenticated:
            main_file = None
            if lecture_id:
                try:
                    main_file = MainFile.objects.get(pk=lecture_id)
                except MainFile.DoesNotExist:
                    return JsonResponse({'response': 'المحاضرة المحددة غير موجودة.'}, status=404)
            
            try:
                # Call the Gemini API processing function
                response_text = self.process_question_with_gemini(request.user, question, main_file, action)
                
                # Save the interaction
                ChatInteraction.objects.create(
                    user=request.user,
                    main_file=main_file,
                    question=question,
                    answer=response_text
                )
                return JsonResponse({'response': response_text})
            
            except Exception as e:
                # Handle any unexpected errors
                return JsonResponse({'response': f'حدث خطأ غير متوقع: {str(e)}'}, status=500)
        
        # If no question or user not authenticated, render the regular list page
        return super().get(request, *args, **kwargs)

    def process_question_with_gemini(self, user, question, file, action):
        """
        Interacts with the Gemini API (gemini-2.0-flash) to get an answer to the question,
        summarize, extract key points, or suggest a study plan.
        """
        # API key will be provided by the Canvas environment, so we leave it empty.
        api_key = "AIzaSyA-EEXM-0biCyfnn-rrXcInPNuwx-i0zs8" 
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        headers = {
            'Content-Type': 'application/json'
        }

        # Build the prompt based on the action and lecture context
        prompt = ""
        if action == 'summarize' and file:
            prompt = f"لخص لي المحاضرة التالية في 3-5 نقاط رئيسية. عنوان المحاضرة: '{file.title}'. وصف المحاضرة: '{file.description or 'لا يوجد وصف'}'. المواضيع الرئيسية: {file.subject.name if file.subject else 'غير محدد'}."
        elif action == 'key_points' and file:
            prompt = f"استخرج أهم 5-7 نقاط رئيسية من المحاضرة التالية. عنوان المحاضرة: '{file.title}'. وصف المحاضرة: '{file.description or 'لا يوجد وصف'}'. المواضيع الرئيسية: {file.subject.name if file.subject else 'غير محدد'}."
        elif action == 'study_plan':
            # For study plan, we'll fetch academic progress data
            academic_progress_data = AcademicProgress.objects.filter(user=user).order_by('-date_recorded')[:5] # Get last 5 entries
            progress_details = []
            for entry in academic_progress_data:
                progress_details.append(f"المادة: {entry.subject.name if entry.subject else 'غير محدد'}, الدرجة: {entry.grade or 'غير مسجلة'}, ملاحظات: {entry.notes or 'لا يوجد'}")
            
            user_goals = user.profile.study_goals if hasattr(user, 'profile') and hasattr(user.profile, 'study_goals') else "تحسين الأداء الأكاديمي العام."
            
            # تم تعديل هذا الجزء لتجنب خطأ f-string
            progress_text = '\n'.join(progress_details) if progress_details else 'لا توجد بيانات تقدم أكاديمي سابقة.'
            prompt = f"""
بصفتك مساعد دراسي ذكي، اقترح خطة دراسية مخصصة لهذا الطالب بناءً على المعلومات التالية:
أهداف الطالب: {user_goals}
أحدث سجلات التقدم الأكاديمي للطالب (آخر 5 مواد):
{progress_text}

يرجى تقديم خطة دراسية تتضمن:
1. توصيات عامة لتحسين الأداء.
2. اقتراحات لمواد أو مجالات محددة تحتاج إلى تركيز بناءً على الدرجات.
3. جدول زمني مقترح (مثلاً، يومي/أسبوعي) مع أمثلة.
4. نصائح للمذاكرة الفعالة.
اجعل الخطة عملية ومبسطة ومحفزة.
"""
        else: # Default action: ask a question
            if file:
                prompt = f"أجب عن السؤال: {question} بناءً على سياق محاضرة بعنوان '{file.title}' ووصفها: '{file.description or 'لا يوجد وصف'}'. مواضيعها الرئيسية: {file.subject.name if file.subject else 'غير محدد'}."
            else:
                prompt = f"أجب عن السؤال: {question} (لا يوجد سياق محاضرة محدد)."

        payload = {
            'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.7, # Adjust creativity
                'maxOutputTokens': 800, # Max length of response
            }
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            result = response.json()
            
            if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                return "خطأ: استجابة غير متوقعة من Gemini API."
        except requests.exceptions.Timeout:
            return "خطأ: انتهت مهلة الاتصال بـ Gemini API."
        except requests.exceptions.ConnectionError:
            return "خطأ: فشل الاتصال بـ Gemini API. يرجى التحقق من اتصالك بالإنترنت أو حالة الخدمة."
        except requests.exceptions.RequestException as e:
            # Handle general request errors
            return f"خطأ في الاتصال بالـ API: {str(e)}"
        except Exception as e:
            # Handle any other unexpected errors during response processing
            return f"خطأ غير متوقع أثناء معالجة استجابة Gemini: {str(e)}"
