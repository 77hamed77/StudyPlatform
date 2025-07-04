# Generated by Django 5.2.3 on 2025-06-21 05:03

import django.db.models.deletion
import files_manager.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FileType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='نوع الملف')),
            ],
            options={
                'verbose_name': 'نوع ملف',
                'verbose_name_plural': 'أنواع الملفات',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Lecturer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='اسم المحاضر')),
            ],
            options={
                'verbose_name': 'محاضر',
                'verbose_name_plural': 'محاضرون',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='اسم المادة')),
            ],
            options={
                'verbose_name': 'مادة دراسية',
                'verbose_name_plural': 'مواد دراسية',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MainFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='عنوان الملف')),
                ('description', models.TextField(blank=True, null=True, verbose_name='الوصف (اختياري)')),
                ('file', models.FileField(upload_to='main_files/%Y/%m/', validators=[files_manager.models.validate_file_extension, files_manager.models.validate_file_size], verbose_name='الملف')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')),
                ('file_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='main_files', to='files_manager.filetype', verbose_name='نوع الملف (اختياري)')),
                ('lecturer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='main_files', to='files_manager.lecturer', verbose_name='المحاضر (اختياري)')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_main_files', to=settings.AUTH_USER_MODEL, verbose_name='رُفع بواسطة (المسؤول)')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='main_files', to='files_manager.subject', verbose_name='المادة الدراسية')),
            ],
            options={
                'verbose_name': 'ملف رئيسي',
                'verbose_name_plural': 'الملفات الرئيسية',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='UserFileInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marked_as_read', models.BooleanField(default=False, verbose_name='تم تمييزه كمقروء/مدروس')),
                ('marked_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ التمييز')),
                ('main_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_interactions_set', to='files_manager.mainfile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_interactions_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'تفاعل مستخدم مع ملف',
                'verbose_name_plural': 'تفاعلات المستخدمين مع الملفات',
                'ordering': ['-marked_at'],
            },
        ),
        migrations.CreateModel(
            name='StudentSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='عنوان الملخص')),
                ('file', models.FileField(upload_to='student_summaries/%Y/%m/', validators=[files_manager.models.validate_file_extension, files_manager.models.validate_file_size], verbose_name='ملف الملخص')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')),
                ('status', models.CharField(choices=[('pending', 'بانتظار المراجعة'), ('approved', 'معتمد'), ('rejected', 'مرفوض')], db_index=True, default='pending', max_length=10, verbose_name='حالة الملخص')),
                ('admin_notes', models.TextField(blank=True, null=True, verbose_name='ملاحظات المشرف (سبب الرفض مثلاً)')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_student_summaries', to=settings.AUTH_USER_MODEL, verbose_name='رُفع بواسطة الطالب')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_summaries', to='files_manager.subject', verbose_name='المادة الدراسية')),
            ],
            options={
                'verbose_name': 'ملخص طالب',
                'verbose_name_plural': 'ملخصات الطلاب',
                'ordering': ['-uploaded_at'],
                'indexes': [models.Index(fields=['uploaded_by', 'status'], name='files_manag_uploade_a7153c_idx'), models.Index(fields=['subject', 'status'], name='files_manag_subject_df51a7_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='mainfile',
            index=models.Index(fields=['subject', '-uploaded_at'], name='files_manag_subject_38d783_idx'),
        ),
        migrations.AddIndex(
            model_name='mainfile',
            index=models.Index(fields=['file_type', '-uploaded_at'], name='files_manag_file_ty_5c93b9_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='userfileinteraction',
            unique_together={('user', 'main_file')},
        ),
    ]
