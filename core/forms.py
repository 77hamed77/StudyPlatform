from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField # إضافة UsernameField
from django.contrib.auth.models import User
from .models import UserProfile
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("البريد الإلكتروني"),
        required=True, # جعل البريد الإلكتروني إلزاميًا عند التسجيل
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email") # تحديد الحقول المطلوبة فقط
        field_classes = {'username': UsernameField} # استخدام UsernameField الأصلي من Django
        widgets = { # إضافة widgets هنا مباشرة
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم مستخدم فريد (حروف وأرقام فقط)')}),
        }

    def clean_email(self): # التحقق من أن البريد الإلكتروني فريد
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
    username = forms.CharField( # استخدام CharField بدلاً من UsernameField إذا أردت تخصيص التحقق
        required=True,
        label=_("اسم المستخدم"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    # يمكنك إضافة حقول First Name و Last Name إذا أردت
    # first_name = forms.CharField(required=False, label=_("الاسم الأول"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    # last_name = forms.CharField(required=False, label=_("الاسم الأخير"), widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email'] # , 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = self.instance.username # حفظ اسم المستخدم الأصلي للتحقق
        self.original_email = self.instance.email # حفظ البريد الإلكتروني الأصلي للتحقق

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username != self.original_username: # تحقق فقط إذا تغير اسم المستخدم
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError(_("اسم المستخدم هذا مأخوذ بالفعل."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != self.original_email: # تحقق فقط إذا تغير البريد الإلكتروني
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(_("هذا البريد الإلكتروني مُستخدم بالفعل."))
        return email


class UserProfileForm(forms.ModelForm):
    dark_mode_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), # استخدام CheckboxInput مباشرة
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