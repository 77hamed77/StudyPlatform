import requests
import os # لاستيراد متغيرات البيئة
from django.shortcuts import render
from django.views.generic import ListView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_GET
from django.db import models # استيراد models لاستخدام models.Q
from files_manager.models import MainFile
from .models import ChatInteraction # التأكد من استيراد ChatInteraction من models.py

class ChatAssistantView(LoginRequiredMixin, ListView):
    template_name = 'chat_assistant/chat_assistant.html'
    context_object_name = 'files'

    def get_queryset(self):
        """
        يسترجع قائمة المحاضرات بناءً على معايير البحث والتصفية.
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
        يضيف بيانات إضافية للسياق، مثل السنوات الدراسية والفصول.
        """
        context = super().get_context_data(**kwargs)
        context['academic_years'] = MainFile.objects.values_list('academic_year', flat=True).distinct().order_by('academic_year')
        context['semesters'] = MainFile.SEMESTER_CHOICES
        return context

    def get(self, request, *args, **kwargs):
        """
        يعالج طلبات GET، بما في ذلك طلبات الشات API.
        """
        question = request.GET.get('question')
        lecture_id = request.GET.get('lecture_id')

        if question and request.user.is_authenticated:
            try:
                main_file = MainFile.objects.get(pk=lecture_id) if lecture_id else None
                
                # استدعاء دالة معالجة السؤال مع OpenRouter
                response_text = self.process_question_with_openrouter(question, main_file)
                
                # حفظ التفاعل
                ChatInteraction.objects.create(
                    user=request.user,
                    main_file=main_file,
                    question=question,
                    answer=response_text
                )
                return JsonResponse({'response': response_text})
            
            except MainFile.DoesNotExist:
                return JsonResponse({'response': 'المحاضرة المحددة غير موجودة.'}, status=404)
            except Exception as e:
                # التعامل مع أي أخطاء أخرى غير متوقعة
                return JsonResponse({'response': f'حدث خطأ غير متوقع: {str(e)}'}, status=500)
        
        # إذا لم يكن هناك سؤال أو لم يكن المستخدم مصادقاً، اعرض صفحة القائمة العادية
        return super().get(request, *args, **kwargs)

    def process_question_with_openrouter(self, question, file):
        """
        يتفاعل مع OpenRouter API للحصول على إجابة على السؤال.
        """
        # قراءة مفتاح API من متغيرات البيئة
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            return "خطأ: مفتاح OpenRouter API غير مهيأ. يرجى إعداد متغير البيئة OPENROUTER_API_KEY."

        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # بناء الـ prompt بناءً على السؤال ونوع المحاضرة
        if file:
            if question == 'ترجم هذه المحاضرة':
                prompt = f"ترجم المحتوى التالي إلى العربية: {file.title} - {file.description or 'لا يوجد وصف'} (افترض أن المحتوى هو نص المحاضرة)."
            elif question == 'لخص لي أهم الأفكار':
                prompt = f"قم بتلخيص أهم الأفكار في محاضرة بعنوان {file.title} بناءً على الوصف: {file.description or 'لا يوجد وصف'}."
            elif question == 'ابحث عن عناوين يوتيوب':
                prompt = f"اقترح عناوين فيديوهات يوتيوب محتملة تتعلق بمحاضرة بعنوان {file.title} وموضوعها {file.subject.name if file.subject else 'غير محدد'} (بدون الوصول المباشر للويب)."
            else:
                prompt = f"أجب عن السؤال: {question} بناءً على محاضرة بعنوان {file.title} ووصفها {file.description or 'لا يوجد وصف'}."
        else:
            prompt = f"أجب عن السؤال: {question} (لا يوجد سياق محاضرة)."

        payload = {
            'model': 'anthropic/claude-3.5-sonnet', # يمكنك تغيير النموذج حسب الحاجة
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 500 # تحديد أقصى عدد من التوكنات للإجابة
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60) # إضافة مهلة زمنية للطلب
            response.raise_for_status() # رفع استثناء لأكواد حالة HTTP 4xx/5xx
            result = response.json()
            
            # التحقق من بنية الاستجابة قبل الوصول إلى المفاتيح
            if 'choices' in result and result['choices'] and 'message' in result['choices'][0] and 'content' in result['choices'][0]['message']:
                return result['choices'][0]['message']['content']
            else:
                return "خطأ: استجابة غير متوقعة من OpenRouter API."
        except requests.exceptions.Timeout:
            return "خطأ: انتهت مهلة الاتصال بـ OpenRouter API."
        except requests.exceptions.ConnectionError:
            return "خطأ: فشل الاتصال بـ OpenRouter API. يرجى التحقق من اتصالك بالإنترنت أو حالة الخدمة."
        except requests.exceptions.RequestException as e:
            # التعامل مع أخطاء الطلب العامة
            return f"خطأ في الاتصال بالـ API: {str(e)}"
        except Exception as e:
            # التعامل مع أي أخطاء أخرى غير متوقعة أثناء معالجة الاستجابة
            return f"خطأ غير متوقع أثناء معالجة استجابة OpenRouter: {str(e)}"

