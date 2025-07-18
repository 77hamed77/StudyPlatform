# Generated by Django 5.2.3 on 2025-07-12 02:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('files_manager', '0003_mainfile_academic_year_mainfile_semester_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivateMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='المحتوى')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='الوقت')),
                ('is_read', models.BooleanField(default=False, verbose_name='مقروءة')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_private_messages', to=settings.AUTH_USER_MODEL, verbose_name='المستلم')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_private_messages', to=settings.AUTH_USER_MODEL, verbose_name='المرسل')),
            ],
            options={
                'verbose_name': 'رسالة خاصة',
                'verbose_name_plural': 'رسائل خاصة',
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='عنوان السؤال')),
                ('content', models.TextField(verbose_name='محتوى السؤال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('upvotes', models.IntegerField(default=0, verbose_name='تصويتات إيجابية')),
                ('downvotes', models.IntegerField(default=0, verbose_name='تصويتات سلبية')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asked_questions', to=settings.AUTH_USER_MODEL, verbose_name='الكاتب')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questions', to='files_manager.subject', verbose_name='المادة')),
            ],
            options={
                'verbose_name': 'سؤال',
                'verbose_name_plural': 'أسئلة',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='محتوى الإجابة')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('upvotes', models.IntegerField(default=0, verbose_name='تصويتات إيجابية')),
                ('downvotes', models.IntegerField(default=0, verbose_name='تصويتات سلبية')),
                ('is_accepted', models.BooleanField(default=False, verbose_name='إجابة مقبولة')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='provided_answers', to=settings.AUTH_USER_MODEL, verbose_name='الكاتب')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='community.question', verbose_name='السؤال')),
            ],
            options={
                'verbose_name': 'إجابة',
                'verbose_name_plural': 'إجابات',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StudyGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='اسم المجموعة')),
                ('description', models.TextField(blank=True, null=True, verbose_name='وصف المجموعة')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_study_groups', to=settings.AUTH_USER_MODEL, verbose_name='المنشئ')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='study_groups', to='files_manager.subject', verbose_name='المادة')),
            ],
            options={
                'verbose_name': 'مجموعة دراسية',
                'verbose_name_plural': 'مجموعات دراسية',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GroupMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='المحتوى')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='الوقت')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_group_messages', to=settings.AUTH_USER_MODEL, verbose_name='المرسل')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='community.studygroup', verbose_name='المجموعة')),
            ],
            options={
                'verbose_name': 'رسالة مجموعة',
                'verbose_name_plural': 'رسائل المجموعات',
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='GroupMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('member', 'عضو'), ('admin', 'مسؤول')], default='member', max_length=20, verbose_name='الدور')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الانضمام')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='community.studygroup', verbose_name='المجموعة')),
            ],
            options={
                'verbose_name': 'عضوية مجموعة',
                'verbose_name_plural': 'عضويات المجموعات',
                'unique_together': {('group', 'user')},
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('vote_type', models.SmallIntegerField(choices=[(1, 'Upvote'), (-1, 'Downvote')], verbose_name='نوع التصويت')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التصويت')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'تصويت',
                'verbose_name_plural': 'تصويتات',
                'unique_together': {('user', 'content_type', 'object_id')},
            },
        ),
    ]
