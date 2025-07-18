# Generated by Django 5.2.3 on 2025-07-12 02:11

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('prayer_times', '0004_prayerreminder_is_notified_evening_adhkar_today_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FavoriteItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.CharField(max_length=255, verbose_name='معرف العنصر')),
                ('item_text', models.TextField(verbose_name='نص العنصر')),
                ('item_category', models.CharField(blank=True, max_length=255, null=True, verbose_name='تصنيف العنصر')),
                ('item_type', models.CharField(max_length=50, verbose_name='نوع العنصر')),
            ],
            options={
                'verbose_name': 'عنصر مفضل',
                'verbose_name_plural': 'عناصر مفضلة',
                'ordering': ['user', 'item_type', 'item_category'],
            },
        ),
        migrations.AlterModelOptions(
            name='location',
            options={'verbose_name': 'الموقع', 'verbose_name_plural': 'المواقع'},
        ),
        migrations.AlterModelOptions(
            name='prayerreminder',
            options={'verbose_name': 'إعدادات تذكير الصلاة', 'verbose_name_plural': 'إعدادات تذكيرات الصلاة'},
        ),
        migrations.AlterModelOptions(
            name='prayertime',
            options={'ordering': ['date', 'time'], 'verbose_name': 'وقت الصلاة', 'verbose_name_plural': 'أوقات الصلاة'},
        ),
        migrations.RemoveIndex(
            model_name='prayertime',
            name='prayer_time_user_id_9025c7_idx',
        ),
        migrations.RemoveField(
            model_name='location',
            name='state',
        ),
        migrations.AlterField(
            model_name='location',
            name='country',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='الدولة'),
        ),
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.FloatField(verbose_name='خط العرض'),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.FloatField(verbose_name='خط الطول'),
        ),
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=255, verbose_name='الاسم'),
        ),
        migrations.AlterField(
            model_name='location',
            name='timezone',
            field=models.CharField(default='Asia/Damascus', max_length=255, verbose_name='المنطقة الزمنية'),
        ),
        migrations.AlterField(
            model_name='prayerreminder',
            name='daily_werd_reminder_enabled',
            field=models.BooleanField(default=False, verbose_name='تمكين تذكير الورد اليومي'),
        ),
        migrations.AlterField(
            model_name='prayerreminder',
            name='daily_werd_reminder_time',
            field=models.TimeField(blank=True, null=True, verbose_name='وقت تذكير الورد اليومي'),
        ),
        migrations.AlterField(
            model_name='prayerreminder',
            name='enabled',
            field=models.BooleanField(default=True, verbose_name='تمكين الإشعارات'),
        ),
        migrations.AlterField(
            model_name='prayerreminder',
            name='last_notification_reset_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='تاريخ آخر إعادة تعيين للإشعارات'),
        ),
        migrations.AlterField(
            model_name='prayerreminder',
            name='notification_time_before',
            field=models.IntegerField(default=10, verbose_name='وقت الإشعار قبل (بالدقائق)'),
        ),
        migrations.AlterField(
            model_name='prayerreminder',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='prayer_reminder_setting', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم'),
        ),
        migrations.AlterField(
            model_name='prayertime',
            name='is_notified',
            field=models.BooleanField(default=False, verbose_name='تم الإشعار'),
        ),
        migrations.AlterField(
            model_name='prayertime',
            name='prayer_type',
            field=models.CharField(choices=[('fajr', 'الفجر'), ('sunrise', 'الشروق'), ('dhuhr', 'الظهر'), ('asr', 'العصر'), ('maghrib', 'المغرب'), ('isha', 'العشاء'), ('imsak', 'الإمساك'), ('midnight', 'منتصف الليل')], max_length=20, verbose_name='نوع الصلاة'),
        ),
        migrations.AlterField(
            model_name='prayertime',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prayer_times', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم'),
        ),
        migrations.AddField(
            model_name='favoriteitem',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='نوع المحتوى'),
        ),
        migrations.AddField(
            model_name='favoriteitem',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorite_items', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم'),
        ),
        migrations.AlterUniqueTogether(
            name='favoriteitem',
            unique_together={('user', 'content_type', 'object_id')},
        ),
    ]
