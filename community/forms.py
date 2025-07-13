from django import forms
from .models import StudyGroup, GroupMessage, GroupMembership
from files_manager.models import Subject # Assuming Subject is here
from django.contrib.auth import get_user_model

User = get_user_model()

class StudyGroupForm(forms.ModelForm):
    """
    نموذج لإنشاء أو تحديث مجموعة دراسية.
    """
    class Meta:
        model = StudyGroup
        fields = ['name', 'subject', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المجموعة الدراسية'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'وصف مختصر للمجموعة...'}),
        }
        labels = {
            'name': 'اسم المجموعة',
            'subject': 'المادة الدراسية',
            'description': 'الوصف',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate subject choices dynamically
        # Ensure Subject model exists and has data
        self.fields['subject'].queryset = Subject.objects.all().order_by('name')
        self.fields['subject'].empty_label = "اختر مادة (اختياري)"


class GroupMessageForm(forms.ModelForm):
    """
    نموذج لإرسال رسالة داخل مجموعة دراسية.
    """
    class Meta:
        model = GroupMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'اكتب رسالتك هنا...'}),
        }
        labels = {
            'content': 'الرسالة',
        }

class GroupMembershipForm(forms.ModelForm):
    """
    نموذج لإدارة عضوية المجموعة (للاستخدام الداخلي أو الإداري).
    """
    class Meta:
        model = GroupMembership
        fields = ['user', 'group', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'user': 'المستخدم',
            'group': 'المجموعة',
            'role': 'الدور',
        }

