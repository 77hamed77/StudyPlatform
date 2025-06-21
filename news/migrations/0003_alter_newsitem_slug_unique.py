# news/migrations/0003_alter_newsitem_slug_unique.py (أو الاسم المشابه)

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_fix_duplicate_slugs'), # <--- عدّل هذا ليعتمد على الـ data migration الجديد
    ]

    operations = [
        migrations.AlterField(
            model_name='newsitem',
            name='slug',
            field=models.SlugField(
                blank=True, # أبقه blank=True إذا كنت تنشئه تلقائيًا
                help_text='يُستخدم في الـ URL، عادةً ما يتم إنشاؤه تلقائيًا من العنوان إذا تُرك فارغًا.',
                max_length=220,
                unique=True, # هذا هو القيد الذي كان يسبب المشكلة
                verbose_name='الاسم اللطيف (Slug) للـ URL'
            ),
        ),
        # ... أي عمليات أخرى قد تكون موجودة في هذا الـ migration ...
    ]