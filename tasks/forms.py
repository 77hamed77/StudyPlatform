# tasks/forms.py
from django import forms
from .models import Task, Subject # استيراد الموديلات من .models
from django.utils.translation import gettext_lazy as _

class TaskForm(forms.ModelForm): # <--- هذا هو النموذج الصحيح
    due_date = forms.DateTimeField(
        label=_("الموعد النهائي (اختياري)"),
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': _('YYYY-MM-DD HH:MM')
            }
        )
    )

    class Meta:
        model = Task # <--- هنا نشير إلى الموديل Task الذي تم استيراده
        fields = ['title', 'description', 'subject', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('مثال: مراجعة الفصل الأول لمادة الرياضيات')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('أضف تفاصيل إضافية عن المهمة هنا...')
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': _('عنوان المهمة'),
            'description': _('الوصف (اختياري)'),
            'subject': _('المادة الدراسية (اختياري)'),
            'status': _('حالة المهمة'),
        }
        help_texts = {
            'title': _('أدخل عنوانًا وصفيًا للمهمة.'),
            'due_date': _('حدد تاريخًا ووقتًا إذا كانت المهمة مرتبطة بموعد محدد.'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if 'subject' in self.fields:
            self.fields['subject'].queryset = Subject.objects.all().order_by('name') # كمثال
            self.fields['subject'].required = False

# **** تأكد من عدم وجود تعريف class Task(models.Model): هنا ****