from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, UsernameField
from django.contrib.auth import get_user_model
from .models import UserProfile, DiscussionPost, DiscussionComment, FAQItem, AcademicProgress, \
    EducationalResourceRating # استيراد EducationalResourceRating
from files_manager.models import Subject
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("البريد الإلكتروني"),
        required=True,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
        field_classes = {'username': UsernameField}
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم مستخدم فريد (حروف وأرقام فقط)')}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("هذا البريد الإلكتروني مُستخدم بالفعل."))
        return email


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label=_("البريد الإلكتروني"),
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )
    username = forms.CharField(
        required=True,
        label=_("اسم المستخدم"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = self.instance.username
        self.original_email = self.instance.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username != self.original_username:
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError(_("اسم المستخدم هذا مأخوذ بالفعل."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != self.original_email:
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(_("هذا البريد الإلكتروني مُستخدم بالفعل."))
        return email


class UserProfileForm(forms.ModelForm):
    dark_mode_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("تفعيل الوضع الليلي")
    )
    pomodoro_work_duration = forms.IntegerField(
        min_value=1, max_value=120, label=_("مدة جلسة العمل (دقائق)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('افتراضي: 25')}),
        help_text=_("أدخل قيمة بين 1 و 120.")
    )
    pomodoro_short_break_duration = forms.IntegerField(
        min_value=1, max_value=60, label=_("مدة الراحة القصيرة (دقائق)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('افتراضي: 5')}),
        help_text=_("أدخل قيمة بين 1 و 60.")
    )
    pomodoro_long_break_duration = forms.IntegerField(
        min_value=1, max_value=90, label=_("مدة الراحة الطويلة (دقائق)"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('افتراضي: 15')}),
        help_text=_("أدخل قيمة بين 1 و 90.")
    )
    pomodoro_sessions_before_long_break = forms.IntegerField(
        min_value=1, max_value=10, label=_("عدد الجلسات قبل الراحة الطويلة"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('افتراضي: 4')}),
        help_text=_("أدخل قيمة بين 1 و 10.")
    )

    class Meta:
        model = UserProfile
        fields = [
            'dark_mode_enabled',
            'pomodoro_work_duration',
            'pomodoro_short_break_duration',
            'pomodoro_long_break_duration',
            'pomodoro_sessions_before_long_break',
        ]

# --- نماذج الويب الجديدة للأدوات والمرافق (من التحديث السابق) ---

class DiscussionPostForm(forms.ModelForm):
    class Meta:
        model = DiscussionPost
        fields = ['title', 'content', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('عنوان المنشور')}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': _('اكتب محتوى منشورك هنا...')}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': _("العنوان"),
            'content': _("المحتوى"),
            'is_anonymous': _("نشر كمجهول"),
        }


class DiscussionCommentForm(forms.ModelForm):
    class Meta:
        model = DiscussionComment
        fields = ['content', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('اكتب تعليقك هنا...')}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'content': _("التعليق"),
            'is_anonymous': _("نشر كمجهول"),
        }


class AcademicProgressForm(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all().order_by('name'),
        label=_("المادة الدراسية"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = AcademicProgress
        fields = ['subject', 'grade', 'notes', 'date_recorded']
        widgets = {
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': _('مثال: 95.50')}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('ملاحظات إضافية (اختياري)')}),
            'date_recorded': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'subject': _("المادة الدراسية"),
            'grade': _("الدرجة"),
            'notes': _("ملاحظات"),
            'date_recorded': _("تاريخ التسجيل"),
        }

# --- نموذج جديد لتقييم الموارد التعليمية ---

class EducationalResourceRatingForm(forms.ModelForm):
    rating = forms.IntegerField(
        label=_("تقييمك"),
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5', 'placeholder': _('التقييم من 1 إلى 5')})
    )
    review_text = forms.CharField(
        label=_("مراجعتك (اختياري)"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('اكتب مراجعتك هنا...')})
    )

    class Meta:
        model = EducationalResourceRating
        fields = ['rating', 'review_text']

