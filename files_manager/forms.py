from django import forms
from django.contrib.auth import get_user_model  # استيراد User
from .models import StudentSummary, Subject
from django.utils.translation import gettext_lazy as _
from .models import validate_file_extension, validate_file_size

User = get_user_model()  # تعيين User كموديل المستخدم الحالي

class StudentSummaryUploadForm(forms.ModelForm):
    title = forms.CharField(
        label=_("عنوان الملخص"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('مثال: ملخص شامل للفصل الأول في الكيمياء'),
            'required': 'required',
        }),
        max_length=255,
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all().order_by('name'),
        label=_("المادة الدراسية"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=_("--- اختر المادة ---"),
        required=True,
    )
    file = forms.FileField(
        label=_("ملف الملخص"),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.zip,.rar,.jpg,.jpeg,.png,.gif'}),
        validators=[validate_file_extension, validate_file_size],
        help_text=_("الملفات المسموح بها: PDF, DOC, DOCX, PPT, PPTX, إلخ. (حجم أقصى: 10MB)"),
    )
    description = forms.CharField(
        label=_("الوصف (اختياري)"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('مثال: ملخص شامل للفصل الأول في الكيمياء'),
        }),
        required=False,
        max_length=1000,
    )
    is_public = forms.BooleanField(
        label=_("مشاركة الملخص مع الجميع"),
        required=False,
        initial=False,
        help_text=_("إذا تم تحديده، سيكون الملخص متاحًا للجميع بعد الموافقة."),
    )
    is_anonymous = forms.BooleanField(
        label=_("رفع الملخص بشكل مجهول"),
        required=False,
        initial=False,
        help_text=_("إذا تم تحديده، سيتم إخفاء اسم المستخدم."),
    )
    uploaded_by = forms.ModelChoiceField(
        queryset=None,
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = StudentSummary
        fields = ['title', 'subject', 'file', 'description', 'is_public', 'is_anonymous', 'uploaded_by']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['uploaded_by'].queryset = User.objects.filter(id=user.id)
            self.fields['uploaded_by'].initial = user

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('file'):
            raise forms.ValidationError(_("يجب رفع ملف للملخص."))
        return cleaned_data