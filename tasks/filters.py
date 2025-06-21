# tasks/filters.py
import django_filters
from django import forms # استيراد forms ضروري لـ widgets
from .models import Task, Subject # لا يتم استيراد STATUS_CHOICES مباشرة
from django.utils.translation import gettext_lazy as _

class TaskFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        lookup_expr='icontains', # للبحث عن جزء من النص (case-insensitive)
        label=_('بحث في العنوان/الوصف'),
        widget=forms.TextInput(attrs={
            'placeholder': _('أدخل كلمة مفتاحية...'),
            # 'class': 'form-control form-control-sm' # سيتم إضافتها في __init__
            })
    )
    subject = django_filters.ModelChoiceFilter(
        queryset=Subject.objects.all().order_by('name'), # جلب جميع المواد مرتبة
        label=_('المادة الدراسية'),
        empty_label=_("كل المواد"), # نص للخيار الفارغ
        # widget=forms.Select(attrs={'class': 'form-select form-select-sm'}) # سيتم إضافتها في __init__
    )
    status = django_filters.ChoiceFilter(
        choices=Task.STATUS_CHOICES, # *** الوصول إلى STATUS_CHOICES عبر كلاس Task ***
        label=_('الحالة'),
        empty_label=_("كل الحالات"),
        # widget=forms.Select(attrs={'class': 'form-select form-select-sm'}) # سيتم إضافتها في __init__
    )
    # يمكنك إضافة فلاتر أخرى هنا، مثل:
    # due_date_gte = django_filters.DateFilter(
    #     field_name='due_date',
    #     lookup_expr='gte',
    #     label=_('الموعد النهائي بعد أو في'),
    #     widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    # )
    # due_date_lte = django_filters.DateFilter(
    #     field_name='due_date',
    #     lookup_expr='lte',
    #     label=_('الموعد النهائي قبل أو في'),
    #     widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    # )

    class Meta:
        model = Task
        fields = ['title', 'subject', 'status'] # الحقول التي تريد أن يظهر لها فلتر تلقائي (إذا لم تعرفها أعلاه)
                                              # بما أننا عرفناها أعلاه، يمكن ترك هذا فارغًا أو تحديد حقول إضافية

    def __init__(self, *args, **kwargs):
        # لا نحتاج لإزالة request من kwargs هنا إذا لم نستخدمه في الفلتر
        super().__init__(*args, **kwargs)
        # إضافة فئات Bootstrap للـ widgets هنا لتوحيد المظهر
        for field_name, field in self.form.fields.items():
            # إضافة فئة عامة لتحكم أفضل في CSS إذا أردت
            # current_class = field.widget.attrs.get('class', '')
            # field.widget.attrs['class'] = f'{current_class} form-control-sm'.strip()

            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-sm'})
            elif isinstance(field.widget, (forms.TextInput, forms.DateInput, forms.DateTimeInput, forms.EmailInput, forms.URLInput, forms.PasswordInput, forms.NumberInput)):
                field.widget.attrs.update({'class': 'form-control form-control-sm'})
            # يمكنك إضافة شروط لأنواع widgets أخرى إذا استخدمتها