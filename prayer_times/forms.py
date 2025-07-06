# prayer_times/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
# من المفترض أن تكون إعدادات التذكير في UserProfile أو نموذج إعدادات المستخدم
# لذا، هذا النموذج سيكون نموذجاً لـ UserProfile أو نموذج إعدادات مخصص.
# مثال إذا كانت الإعدادات في UserProfile:
# from core.models import UserProfile

class ReminderSettingsForm(forms.Form): # أو forms.ModelForm إذا كانت لنموذج
    minutes_before_prayer = forms.IntegerField(
        label=_("التذكير قبل الصلاة (بالدقائق)"),
        min_value=0,
        max_value=60,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    enable_notifications = forms.BooleanField(
        label=_("تفعيل التذكيرات الصوتية"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )