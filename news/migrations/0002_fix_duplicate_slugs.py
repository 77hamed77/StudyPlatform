# news/migrations/0002_fix_duplicate_slugs.py

from django.db import migrations
from django.utils.text import slugify

def make_slugs_unique(apps, schema_editor):
    NewsItem = apps.get_model('news', 'NewsItem')
    # لا حاجة لـ User هنا لهذه العملية المحددة

    # جلب جميع الأخبار، يفضل ترتيبها لضمان سلوك متسق إذا كان هناك تعديلات متعددة
    all_news_items_for_slug_fix = list(NewsItem.objects.all().order_by('publication_date', 'id'))

    processed_slugs = {} # لتتبع الـ slugs التي تم تعديلها بالفعل وتجنب تكرار العمليات

    for item in all_news_items_for_slug_fix:
        original_slug_value_before_fix = item.slug # حفظ القيمة الأصلية للمقارنة لاحقًا

        # الخطوة 1: إنشاء slug إذا كان فارغًا
        if not item.slug:
            if item.title:
                item.slug = slugify(item.title, allow_unicode=True)
            else: # عنوان فارغ، استخدم ID كحل بديل
                item.slug = f"news-item-{item.id}"
            
            # إذا كان slugify ينتج سلسلة فارغة (مثلاً العنوان كان فقط رموزًا)
            if not item.slug:
                 item.slug = f"news-item-{item.id}"


        # الخطوة 2: ضمان التفرد
        current_slug_to_check = item.slug
        counter = 1
        
        # تحقق مما إذا كان هذا الـ slug (بشكله الحالي أو بعد التعديل الأولي)
        # موجود بالفعل لكائن آخر غير الكائن الحالي
        while NewsItem.objects.filter(slug=current_slug_to_check).exclude(pk=item.pk).exists():
            # إذا كان مكررًا، أضف لاحقة رقمية
            current_slug_to_check = f"{item.slug}-{counter}" # استخدم item.slug (الذي قد يكون تم تعديله في الخطوة 1)
            counter += 1
        
        # إذا تغير الـ slug (سواء بسبب الإنشاء الأولي أو إضافة اللاحقة)
        if current_slug_to_check != original_slug_value_before_fix or not original_slug_value_before_fix:
            item.slug = current_slug_to_check # تحديث الـ slug في الكائن
            item.save(update_fields=['slug']) # حفظ الحقل المحدث فقط


def reverse_slug_changes(apps, schema_editor):
    # هذا الـ migration مصمم ليكون للأمام فقط.
    # عكس هذا التغيير بشكل آمن يتطلب تخزين الـ slugs الأصلية، وهو أمر معقد.
    # للتبسيط، سنتركه فارغًا.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'), # <--- تأكد أن هذا هو اسم الـ migration السابق الفعلي لـ news
                                  # إذا كان لديك migrations أخرى قبل هذا، قم بتحديث هذا السطر
    ]

    operations = [
        migrations.RunPython(make_slugs_unique, reverse_code=reverse_slug_changes),
    ]
    