from django import forms
from .models import StudentSummary, Subject # استيراد Subject
from django.utils.translation import gettext_lazy as _
from .models import validate_file_extension, validate_file_size # استيراد المدققات

class StudentSummaryUploadForm(forms.ModelForm):
    title = forms.CharField(
        label=_("عنوان الملخص"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('مثال: ملخص شامل للفصل الأول في الكيمياء')
        })
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all().order_by('name'), # عرض جميع المواد مرتبة
        label=_("المادة الدراسية"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=_("--- اختر المادة ---")
    )
    file = forms.FileField(
        label=_("ملف الملخص"),
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        validators=[validate_file_extension, validate_file_size], # تطبيق المدققات هنا أيضًا
        help_text=_("الملفات المسموح بها: PDF, DOC, DOCX, PPT, PPTX, إلخ. (حجم أقصى: 10MB)")
    )

    class Meta:
        model = StudentSummary
        fields = ['title', 'subject', 'file']
        # لا حاجة لـ widgets هنا لأننا عرفناها للحقول أعلاه

    # يمكنك إضافة أي تحقق إضافي خاص بالنموذج هنا إذا أردت
    # def clean_title(self):
    #     title = self.cleaned_data.get('title')
    #     # ... أي منطق تحقق ...
    #     return title