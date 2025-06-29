from django import forms
from .models import StudentSummary, Subject  # استيراد Subject
from django.utils.translation import gettext_lazy as _
from .models import validate_file_extension, validate_file_size  # استيراد المدققات

class StudentSummaryUploadForm(forms.ModelForm):
    title = forms.CharField(
        label=_("عنوان الملخص"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('مثال: ملخص شامل للفصل الأول في الكيمياء')
        })
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all().order_by('name'),
        label=_("المادة الدراسية"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=_("--- اختر المادة ---")
    )
    file = forms.FileField(
        label=_("ملف الملخص"),
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        validators=[validate_file_extension, validate_file_size],
        help_text=_("الملفات المسموح بها: PDF, DOC, DOCX, PPT, PPTX, إلخ. (حجم أقصى: 10MB)")
    )

    class Meta:
        model = StudentSummary
        fields = ['title', 'subject', 'file']

    # تحقق إضافي اختياري (لا حاجة لتعديل لأجل Backblaze/S3)
    # إذا أردت منع الملفات المكررة بناءً على الاسم أو أي منطق آخر أضفه هنا

    # مثال: منع رفع ملف بنفس الاسم للمادة نفسها من نفس المستخدم
    # def clean(self):
    #     cleaned_data = super().clean()
    #     title = cleaned_data.get('title')
    #     subject = cleaned_data.get('subject')
    #     file = cleaned_data.get('file')
    #     user = self.initial.get('user')  # مرر المستخدم عند تهيئة الفورم لو احتجت
    #     if StudentSummary.objects.filter(title=title, subject=subject, uploaded_by=user).exists():
    #         raise forms.ValidationError(_("لقد قمت مسبقاً برفع ملخص بهذا العنوان لهذه المادة."))
    #     return cleaned_data