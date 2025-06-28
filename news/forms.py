from django import forms
from .models import NewsItem, NewsCategory
from django.utils.translation import gettext_lazy as _

class NewsItemForm(forms.ModelForm):
    title = forms.CharField(
        label=_("عنوان الخبر"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل عنوانًا جذابًا للخبر')
        })
    )
    slug = forms.SlugField(
        label=_("الاسم اللطيف (Slug) للـ URL"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اتركه فارغًا ليتم إنشاؤه تلقائيًا، أو أدخل اسمًا فريدًا (حروف إنجليزية، أرقام، شرطات)')
        }),
        help_text=_("إذا تُرك فارغًا، سيتم إنشاؤه من العنوان. استخدم حروفًا وأرقامًا وشرطات فقط إذا أدخلته يدويًا.")
    )
    content = forms.CharField(
        label=_("محتوى الخبر الكامل"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 12,
            'placeholder': _('اكتب محتوى الخبر هنا بالتفصيل...')
        })
    )
    excerpt = forms.CharField(
        label=_("مقتطف قصير (اختياري)"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('مقدمة موجزة للخبر (تظهر في القوائم)...')
        }),
        help_text=_("إذا تُرك فارغًا، سيتم إنشاء مقتطف تلقائيًا من المحتوى.")
    )
    category = forms.ModelChoiceField(
        queryset=NewsCategory.objects.all().order_by('name'),
        label=_("تصنيف الخبر"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=_("--- اختر تصنيفًا (اختياري) ---")
    )
    image = forms.ImageField(
        label=_("صورة الخبر (اختياري)"),
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    publication_date = forms.DateTimeField(
        label=_("تاريخ ووقت النشر"),
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        ),
        required=False,
        help_text=_("إذا تُرك فارغًا، سيتم استخدام التاريخ والوقت الحاليين عند النشر الفعلي.")
    )
    is_important = forms.BooleanField(
        label=_("تمييز كخبر مهم (سيظهر بشكل بارز)؟"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_published = forms.BooleanField(
        label=_("نشر هذا الخبر على الموقع؟"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("إلغاء التحديد لإبقاء الخبر كمسودة.")
    )

    class Meta:
        model = NewsItem
        fields = [
            'title',
            'slug',
            'content',
            'excerpt',
            'category',
            'image',
            'publication_date',
            'is_important',
            'is_published',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.image:
            pass
        # لا حاجة لتغيير قيمة initial هنا، الموديل سيعالجها

class NewsCategoryForm(forms.ModelForm):
    name = forms.CharField(
        label=_("اسم التصنيف"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('مثال: أكاديمي، فعاليات، إعلانات هامة')
        })
    )
    slug = forms.SlugField(
        label=_("الاسم اللطيف (Slug) للـ URL"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اتركه فارغًا ليتم إنشاؤه تلقائيًا')
        }),
        help_text=_("إذا تُرك فارغًا، سيتم إنشاؤه من الاسم. استخدم حروفًا وأرقامًا وشرطات فقط إذا أدخلته يدويًا.")
    )

    class Meta:
        model = NewsCategory
        fields = ['name', 'slug']