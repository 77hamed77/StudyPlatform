from django import forms
from .models import QuickNote, NoteCategory
from django.utils.translation import gettext_lazy as _

class QuickNoteForm(forms.ModelForm):
    title = forms.CharField(
        label=_("عنوان الملاحظة"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل عنوانًا مميزًا لملاحظتك...')
        })
    )
    content = forms.CharField(
        label=_("محتوى الملاحظة"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8, # زيادة عدد الأسطر قليلاً
            'placeholder': _('اكتب محتوى ملاحظتك هنا...')
        })
    )
    category = forms.ModelChoiceField(
        queryset=NoteCategory.objects.none(), # سيتم تحديثه في __init__
        required=False, # التصنيف اختياري
        label=_("التصنيف (اختياري)"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=_("--- اختر تصنيفًا ---") # نص للخيار الفارغ
    )

    class Meta:
        model = QuickNote
        fields = ['title', 'content', 'category']
        # لا حاجة لـ widgets هنا لأننا عرفناها للحقول أعلاه

    def __init__(self, *args, **kwargs):
        # الحصول على المستخدم من keyword arguments الممررة من الـ view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            # فلترة حقل التصنيف ليُظهر فقط التصنيفات الخاصة بالمستخدم الحالي
            self.fields['category'].queryset = NoteCategory.objects.filter(user=self.user).order_by('name')
        else:
            # إذا لم يتم تمرير المستخدم (مثلاً في Django Admin أو حالة نادرة)
            self.fields['category'].queryset = NoteCategory.objects.none()
            self.fields['category'].disabled = True # تعطيل الحقل


class NoteCategoryForm(forms.ModelForm):
    name = forms.CharField(
        label=_("اسم التصنيف"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('مثال: أفكار، مهام شخصية، روابط هامة...')
        }),
        help_text=_("اختر اسمًا وصفيًا للتصنيف.")
    )

    class Meta:
        model = NoteCategory
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # الحصول على المستخدم
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        # التحقق من أن اسم التصنيف فريد للمستخدم الحالي (بالإضافة لـ unique_together في الموديل)
        # unique_together في الموديل سيمنع الحفظ، لكن هذا التحقق يظهر خطأً أفضل في النموذج
        if self.user:
            query = NoteCategory.objects.filter(user=self.user, name__iexact=name)
            if self.instance and self.instance.pk: # في حالة التعديل، استثنِ الكائن الحالي
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError(_("لديك تصنيف بهذا الاسم بالفعل."))
        return name