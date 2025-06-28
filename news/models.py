from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import os

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif']
    if not ext.lower() in valid_extensions:
        raise models.ValidationError(_(f"امتداد الملف '{ext}' غير مدعوم. الامتدادات المسموح بها: {', '.join(valid_extensions)}"))

def validate_file_size(value):
    limit = 10 * 1024 * 1024  # 10MB
    if value.size > limit:
        raise models.ValidationError(_(f"حجم الملف كبير جدًا. الحد الأقصى المسموح به هو {limit / (1024*1024):.0f}MB."))

class NewsCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("اسم التصنيف"))
    slug = models.SlugField(max_length=120, unique=True, verbose_name=_("الاسم اللطيف (Slug)"), help_text=_("يُستخدم في الـ URL..."))
    class Meta:
        verbose_name = _("تصنيف خبر"); verbose_name_plural = _("تصنيفات الأخبار"); ordering = ['name']
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse('news:news_list_by_category', kwargs={'category_slug': self.slug})
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

class NewsItem(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("عنوان الخبر"))
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name=_("الاسم اللطيف (Slug) للـ URL"),
        help_text=_("يُستخدم في الـ URL، عادةً ما يتم إنشاؤه تلقائيًا من العنوان إذا تُرك فارغًا.")
    )
    content = models.TextField(verbose_name=_("محتوى الخبر"))
    excerpt = models.TextField(blank=True, verbose_name=_("مقتطف (اختياري)"), help_text=_("مقدمة قصيرة..."))
    category = models.ForeignKey(NewsCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='news_items', verbose_name=_("التصنيف"))
    image = models.ImageField(upload_to='news_images/%Y/%m/', blank=True, null=True, verbose_name=_("صورة الخبر (اختياري)"), validators=[validate_file_size])
    publication_date = models.DateTimeField(default=timezone.now, verbose_name=_("تاريخ النشر"), db_index=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='authored_news', verbose_name=_("الناشر"))
    is_important = models.BooleanField(default=False, verbose_name=_("خبر مهم (مثبت)؟"), db_index=True, help_text=_("الأخبار الهامة..."))
    is_published = models.BooleanField(default=True, verbose_name=_("منشور؟"), db_index=True, help_text=_("إلغاء التحديد..."))

    class Meta:
        verbose_name = _("خبر/إعلان"); verbose_name_plural = _("الأخبار والإعلانات"); ordering = ['-publication_date']
        indexes = [models.Index(fields=['slug', 'publication_date']), models.Index(fields=['-publication_date', 'is_published', 'is_important'])]
    def __str__(self): return self.title
    def get_absolute_url(self):
        return reverse('news:news_detail', kwargs={'year': self.publication_date.year, 'month': self.publication_date.month, 'day': self.publication_date.day, 'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title, allow_unicode=True)
            original_slug_for_uniqueness_check = self.slug
            counter = 1
            queryset = NewsItem.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug_for_uniqueness_check}-{counter}"
                counter += 1
        if not self.excerpt and self.content:
            from django.utils.html import strip_tags
            self.excerpt = strip_tags(self.content)[:150] + "..."
        # إضافة هذا السطر لحل مشكلة النشر إذا تُرك الحقل فارغًا
        if not self.publication_date:
            self.publication_date = timezone.now()
        super().save(*args, **kwargs)