# news/forms.py
from django import forms
from .models import NewsItem, NewsCategory # استيراد الموديلات
from django.utils.translation import gettext_lazy as _

class NewsItemForm(forms.ModelForm):
    title = forms.CharField(
        label=_("عنوان الخبر"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل عنوانًا جذابًا للخبر')
        })
    )
    slug = forms.SlugField( # حقل الـ Slug
        label=_("الاسم اللطيف (Slug) للـ URL"),
        required=False, # جعله غير إلزامي ليتم إنشاؤه تلقائيًا من الموديل
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
            'rows': 12, # زيادة عدد الأسطر
            'placeholder': _('اكتب محتوى الخبر هنا بالتفصيل...')
        })
        # يمكنك إضافة widget لمحرر نصوص متقدم هنا (مثل CKEditorWidget أو TinyMCEWidget)
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
        required=False, # جعل التصنيف اختياريًا
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=_("--- اختر تصنيفًا (اختياري) ---")
    )
    image = forms.ImageField(
        label=_("صورة الخبر (اختياري)"),
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}) # استخدام ClearableFileInput
    )
    publication_date = forms.DateTimeField(
        label=_("تاريخ ووقت النشر"),
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M' # التنسيق المتوقع من datetime-local
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
        required=False, # القيمة الافتراضية في الموديل هي True
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("إلغاء التحديد لإبقاء الخبر كمسودة.")
    )

    class Meta:
        model = NewsItem
        fields = [
            'title',
            'slug', # تضمين slug في الحقول
            'content',
            'excerpt',
            'category',
            'image',
            'publication_date',
            'is_important',
            'is_published',
        ]
        # labels و help_texts و widgets تم تعريفها للحقول أعلاه مباشرة

    def __init__(self, *args, **kwargs):
        # يمكنك تمرير المستخدم للنموذج إذا كنت ستحتاجه لأي منطق خاص
        # self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        # إذا كان النموذج لتعديل كائن موجود وكان لديه صورة، يمكنك عرضها
        if self.instance and self.instance.pk and self.instance.image:
            # هذا يتم التعامل معه عادة في القالب لعرض الصورة الحالية
            pass

        # إذا لم يتم توفير تاريخ نشر، يمكنك تعيينه افتراضيًا للوقت الحالي
        # (الموديل يعتني بهذا إذا كان required=False و default=timezone.now)
        # if not self.initial.get('publication_date') and not (self.instance and self.instance.pk):
        #     from django.utils import timezone
        #     self.initial['publication_date'] = timezone.now()

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
        required=False, # جعله غير إلزامي
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('اتركه فارغًا ليتم إنشاؤه تلقائيًا')
        }),
        help_text=_("إذا تُرك فارغًا، سيتم إنشاؤه من الاسم. استخدم حروفًا وأرقامًا وشرطات فقط إذا أدخلته يدويًا.")
    )

    class Meta:
        model = NewsCategory
        fields = ['name', 'slug']